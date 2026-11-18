"""Bluetooth Low Energy (BLE) client for Plaud NotePin (Realtek 0x005d) and Plaud Note (Nordic 0x0059).

Provides device discovery, battery & storage telemetry, clock synchronization, direct BLE audio
download, and local Wi-Fi transfer activation using `bleak` on Windows, macOS, and Linux.
"""
from __future__ import annotations

import asyncio
import struct
import time
from typing import Any, Callable

try:
    from bleak import BleakClient, BleakScanner
except ImportError:  # pragma: no cover
    BleakClient = None  # type: ignore[assignment,misc]
    BleakScanner = None  # type: ignore[assignment,misc]

SERVICE_UUID = "00001910-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID = "00002bb1-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "00002bb0-0000-1000-8000-00805f9b34fb"
BATTERY_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

COMPANY_NORDIC = 0x0059   # Plaud Note
COMPANY_REALTEK = 0x005D  # Plaud NotePin

AUTH_PREFIX = bytes.fromhex("010100020000")
BULK_END_SENTINEL = 0xFFFFFFFF


class BlePinError(Exception):
    pass


def classify_device(name: str, company_ids: list[int], service_uuids: list[str]) -> str | None:
    upper = (name or "").upper()
    has_service = any(u.lower().startswith("00001910") for u in service_uuids)
    if COMPANY_REALTEK in company_ids:
        return "Plaud NotePin (Realtek)"
    if COMPANY_NORDIC in company_ids or "PLAUD" in upper:
        return "Plaud Note (Nordic)"
    if has_service:
        return "Plaud Compatible Device"
    return None


async def scan_devices(timeout: float = 6.0, include_all: bool = False) -> list[dict[str, Any]]:
    discovered = await BleakScanner.discover(timeout=timeout, return_adv=True)
    results: list[dict[str, Any]] = []

    for _key, (dev, adv) in discovered.items():
        mdata = adv.manufacturer_data or {}
        cids = list(mdata.keys())
        suuids = list(adv.service_uuids or [])
        name = adv.local_name or dev.name or ""
        model = classify_device(name, cids, suuids)
        if not model and not include_all:
            continue

        primary_cid = (
            COMPANY_REALTEK if COMPANY_REALTEK in cids else
            COMPANY_NORDIC if COMPANY_NORDIC in cids else
            (cids[0] if cids else None)
        )
        mhex = mdata[primary_cid].hex() if primary_cid is not None and primary_cid in mdata else ""

        results.append({
            "address": dev.address,
            "name": name or "Unnamed BLE Device",
            "model": model or "Other BLE Device",
            "is_plaud": bool(model),
            "rssi": adv.rssi,
            "company_id": primary_cid,
            "manufacturer_hex": mhex,
        })

    results.sort(key=lambda d: (0 if d["is_plaud"] else 1, -(d["rssi"] if d["rssi"] is not None else -120)))
    return results


async def _connect_with_retry(address: str, attempts: int = 3, wait_s: float = 4.0) -> BleakClient:
    last_err: Exception | None = None
    for idx in range(attempts):
        try:
            client = BleakClient(address, timeout=18.0)
            await client.connect()
            return client
        except Exception as exc:
            last_err = exc
            if idx < attempts - 1:
                await asyncio.sleep(wait_s)
    raise BlePinError(
        f"Could not connect to device ({address}) via Bluetooth. "
        f"Make sure it is awake, nearby, and disconnected from your phone app. ({type(last_err).__name__})"
    )


async def _authenticate_and_probe(client: BleakClient, token: str, queue: asyncio.Queue[bytes]) -> dict[str, Any]:
    await client.write_gatt_char(WRITE_CHAR_UUID, AUTH_PREFIX + token.encode("ascii"), response=False)
    deadline = time.monotonic() + 6.0
    auth_ok = False
    while time.monotonic() < deadline:
        remaining = max(0.1, deadline - time.monotonic())
        try:
            pkt = await asyncio.wait_for(queue.get(), timeout=remaining)
        except asyncio.TimeoutError:
            break
        if len(pkt) >= 4 and pkt[:3] == b"\x01\x01\x00":
            if pkt[3] != 0:
                raise BlePinError("Device rejected the authentication token. Double-check your saved key.")
            auth_ok = True
            break
    if not auth_ok:
        raise BlePinError("Connected over Bluetooth, but the device did not reply to authentication.")

    info: dict[str, Any] = {"authenticated": True}

    try:
        bat = await client.read_gatt_char(BATTERY_CHAR_UUID)
        if bat:
            info["battery"] = int(bat[0])
    except Exception:
        pass

    async def control_cmd(opcode: int, payload: bytes = b"", timeout: float = 2.5) -> bytes:
        # Drain stale frames before issuing a command
        while not queue.empty():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        await client.write_gatt_char(WRITE_CHAR_UUID, struct.pack("<BH", 0x01, opcode) + payload, response=False)
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                pkt = await asyncio.wait_for(queue.get(), timeout=max(0.1, end - time.monotonic()))
            except asyncio.TimeoutError:
                break
            if len(pkt) >= 3 and pkt[0] == 0x01 and struct.unpack_from("<H", pkt, 1)[0] == opcode:
                return pkt[3:]
        return b""

    # Sync device real-time clock (opcode 0x0004)
    now_ts = int(time.time())
    tz_min = int(-time.timezone / 60) if not time.localtime().tm_isdst else int(-time.altzone / 60)
    clock_resp = await control_cmd(0x0004, struct.pack("<Ibb", now_ts, int(tz_min / 60), abs(tz_min) % 60))
    if len(clock_resp) >= 4:
        info["clock_synced"] = True

    # Read storage stats (opcode 0x0006)
    st_resp = await control_cmd(0x0006)
    if len(st_resp) >= 16:
        free_b, total_b = struct.unpack_from("<QQ", st_resp, 0)
        if 0 < total_b < 256 * 1024**3 and free_b <= total_b:
            info["free_bytes"] = free_b
            info["total_bytes"] = total_b
        elif len(st_resp) >= 20:
            used_blocks = struct.unpack_from("<I", st_resp, 2)[0]
            total_blocks = struct.unpack_from("<I", st_resp, 10)[0]
            cap_bytes = struct.unpack_from("<I", st_resp, 16)[0]
            if total_blocks > 0 and cap_bytes > 0:
                used_b = (cap_bytes * used_blocks) // total_blocks
                info["total_bytes"] = cap_bytes
                info["free_bytes"] = max(0, cap_bytes - used_b)

    return info


async def verify_and_read_status(address: str, token: str) -> dict[str, Any]:
    queue: asyncio.Queue[bytes] = asyncio.Queue()
    client = await _connect_with_retry(address)
    try:
        await client.start_notify(NOTIFY_CHAR_UUID, lambda _h, data: queue.put_nowait(bytes(data)))
        await asyncio.sleep(0.15)
        return await _authenticate_and_probe(client, token, queue)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def open_wifi_hotspot(address: str, token: str) -> dict[str, Any]:
    """Authenticate via BLE, sync clock, read telemetry, and trigger opcode 0x000A (Wi-Fi hotspot)."""
    queue: asyncio.Queue[bytes] = asyncio.Queue()
    client = await _connect_with_retry(address, attempts=5, wait_s=5.0)
    try:
        await client.start_notify(NOTIFY_CHAR_UUID, lambda _h, data: queue.put_nowait(bytes(data)))
        await asyncio.sleep(0.15)
        info = await _authenticate_and_probe(client, token, queue)

        while not queue.empty():
            queue.get_nowait()

        await client.write_gatt_char(WRITE_CHAR_UUID, bytes([0x01, 0x0A, 0x00]), response=False)
        ssid = ""
        password = ""
        end = time.monotonic() + 3.5
        while time.monotonic() < end:
            try:
                pkt = await asyncio.wait_for(queue.get(), timeout=max(0.1, end - time.monotonic()))
            except asyncio.TimeoutError:
                break
            if len(pkt) > 5 and pkt[:3] == b"\x01\x0a\x00" and pkt[3] == 0:
                n = pkt[4]
                ssid = pkt[5:5 + n].decode("utf-8", errors="replace")
                m = pkt[5 + n] if len(pkt) > 5 + n else 0
                password = pkt[6 + n:6 + n + m].decode("utf-8", errors="replace")
                break

        info["ssid"] = ssid
        info["password"] = password
        return info
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def ble_list_and_download(
    address: str,
    token: str,
    download_ids: list[int] | None = None,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """List unsynced recordings over BLE (0x001A) and optionally download raw Opus via 0x001C."""
    queue: asyncio.Queue[bytes] = asyncio.Queue()
    client = await _connect_with_retry(address)
    try:
        await client.start_notify(NOTIFY_CHAR_UUID, lambda _h, data: queue.put_nowait(bytes(data)))
        await asyncio.sleep(0.15)
        info = await _authenticate_and_probe(client, token, queue)
        if on_progress:
            on_progress({"ev": "info", **info})

        # Query BLE file list (opcode 0x001A)
        while not queue.empty():
            queue.get_nowait()
        req = struct.pack("<BHIIB", 0x01, 0x001A, int(time.time()), 0, 0)
        await client.write_gatt_char(WRITE_CHAR_UUID, req, response=False)

        batches: list[bytes] = []
        while True:
            wait_t = 4.0 if not batches else 1.8
            try:
                pkt = await asyncio.wait_for(queue.get(), timeout=wait_t)
            except asyncio.TimeoutError:
                break
            if len(pkt) >= 3 and pkt[:3] == b"\x01\x1a\x00":
                batches.append(pkt[3:])

        files: dict[int, int] = {}
        for resp in batches:
            if len(resp) < 8:
                continue
            total_files = struct.unpack_from("<H", resp, 4)[0]
            if total_files == 0:
                continue
            data_len = len(resp) - 8
            entry_size = max(8, data_len // total_files)
            off = 8
            while off + 8 <= len(resp) and len(files) < total_files:
                fid, fsz = struct.unpack_from("<II", resp, off)
                files[fid] = fsz
                off += entry_size

        rec_list = [{"id": str(fid), "size_bytes": fsz} for fid, fsz in files.items()]
        if on_progress:
            on_progress({"ev": "list", "recordings": rec_list})

        downloaded: dict[str, bytes] = {}
        targets = download_ids if download_ids is not None else []
        for fid in targets:
            expected_size = files.get(fid, 10 * 1024 * 1024)
            while not queue.empty():
                queue.get_nowait()
            trigger = struct.pack("<BHIII", 0x01, 0x001C, fid, 0, expected_size)
            await client.write_gatt_char(WRITE_CHAR_UUID, trigger, response=False)

            buf = bytearray()
            last_emit = 0.0
            while True:
                pkt = await asyncio.wait_for(queue.get(), timeout=12.0)
                if not pkt or pkt[0] != 0x02 or len(pkt) < 10:
                    continue
                pkt_fid, pkt_off = struct.unpack_from("<II", pkt, 1)
                if pkt_fid != fid:
                    continue
                if pkt_off == BULK_END_SENTINEL:
                    break
                buf.extend(pkt[10:])
                now_m = time.monotonic()
                if on_progress and now_m - last_emit > 0.4:
                    last_emit = now_m
                    on_progress({
                        "ev": "progress",
                        "id": str(fid),
                        "received": len(buf),
                        "total": expected_size if fid in files else len(buf),
                    })
            downloaded[str(fid)] = bytes(buf)

        return {"info": info, "recordings": rec_list, "downloaded": downloaded}
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
