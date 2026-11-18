"""High-speed local Wi-Fi transfer (~800 kB/s) for Plaud NotePin / Note on Windows and Linux.

Flow:
1. Saves the user's current Wi-Fi profile (`netsh wlan` on Windows, `nmcli` on Linux).
2. Starts a local WebSocket server on port 8081.
3. Sends BLE opcode 0x000A (`open_wifi_hotspot`) to activate the recorder's temporary Wi-Fi AP.
4. Connects the PC's Wi-Fi adapter to the recorder's AP, transfers requested recordings in RAM,
   converts them directly to clean `.wav` files, deletes the temporary AP profile, and restores
   the PC's original home Wi-Fi connection automatically.
"""
from __future__ import annotations

import asyncio
import json
import os
import ipaddress
import re
import socket
import struct
import subprocess
import sys
import tempfile
import time
import xml.sax.saxutils as saxutils
from pathlib import Path
from typing import Any, Callable

try:
    from websockets.asyncio.server import serve
except ImportError:  # pragma: no cover
    serve = None  # type: ignore[assignment]

from . import audio, ble_client

WS_PORT = 8081
MSG_HANDSHAKE = 1
MSG_HELLO = 2
MSG_HEARTBEAT = 3
MSG_WIFI_CLOSE = 4
MSG_FILE_LIST = 11
MSG_FILE_SYNC = 12
MSG_FILE_CONTENT = 13
MSG_FILE_DELETE = 14


class WifiSyncError(Exception):
    pass


def pack_ws_frame(msg_type: int, payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    total_len = len(body) + 8
    header = bytes([total_len & 0xFF, (total_len >> 8) & 0xFF, (total_len >> 16) & 0xFF, 1])
    return header + struct.pack("<HH", msg_type, len(body)) + body


def unpack_ws_frame(raw: bytes) -> tuple[int, dict[str, Any], bytes]:
    if len(raw) < 8:
        raise WifiSyncError("Malformed WebSocket frame from device.")
    msg_type, json_len = struct.unpack_from("<HH", raw, 4)
    meta = json.loads(raw[8:8 + json_len] or b"{}")
    binary = raw[8 + json_len:]
    return msg_type, meta, binary


# ---------------------------------------------------------------------------
# Cross-platform Wi-Fi adapter switching (Windows netsh + Linux nmcli)
# ---------------------------------------------------------------------------

def local_ipv4_addresses() -> set[str]:
    """Best-effort set of this computer's current IPv4 addresses (no packets are sent)."""
    ips: set[str] = set()
    try:
        ips.update(info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 9))  # UDP connect only picks the outgoing interface
            ips.add(probe.getsockname()[0])
    except OSError:
        pass
    return {ip for ip in ips if not ip.startswith("127.")}


def is_device_peer(remote_ip: str, local_ip: str, home_ips: set[str]) -> bool:
    """True if a WebSocket client looks like the recorder on its own hotspot.

    The recorder reaches us on the address we got from ITS access point: that local address is new
    (not one we had on the home network) and the peer sits in the same /24. A machine on the home
    LAN, or on public Wi-Fi before we switched, fails this check and never sees the device token.
    """
    try:
        remote = ipaddress.ip_address(remote_ip.split("%")[0])
        local = ipaddress.ip_address(local_ip.split("%")[0])
    except ValueError:
        return False
    if isinstance(remote, ipaddress.IPv6Address) and remote.ipv4_mapped:
        remote = remote.ipv4_mapped
    if isinstance(local, ipaddress.IPv6Address) and local.ipv4_mapped:
        local = local.ipv4_mapped
    if remote.version != 4 or local.version != 4 or remote.is_loopback:
        return False
    if str(local) in home_ips:
        return False
    return remote in ipaddress.ip_network(f"{local}/24", strict=False)


def _run_cmd(cmd: list[str], timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    kwargs: dict[str, Any] = {"capture_output": True, "text": True, "timeout": timeout, "encoding": "utf-8", "errors": "replace"}
    if sys.platform == "win32":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(cmd, **kwargs)


def scan_visible_ssids() -> list[str]:
    """Return currently visible Wi-Fi SSIDs (works on Windows and Linux regardless of OS language)."""
    ssids: list[str] = []
    if sys.platform == "win32":
        res = _run_cmd(["netsh", "wlan", "show", "networks"])
        for line in res.stdout.splitlines():
            m = re.match(r"^\s*SSID\s+\d+\s*:\s*(.+?)\s*$", line)
            if m and m.group(1) and m.group(1) not in ssids:
                ssids.append(m.group(1))
    elif sys.platform.startswith("linux"):
        _run_cmd(["nmcli", "dev", "wifi", "rescan"], timeout=15)
        res = _run_cmd(["nmcli", "-t", "-f", "SSID", "dev", "wifi", "list"], timeout=15)
        for line in res.stdout.splitlines():
            s = line.strip()
            if s and s not in ssids:
                ssids.append(s)
    return ssids


def get_current_wifi_profile() -> str:
    """Detect currently active Wi-Fi profile/SSID so we can restore it after sync."""
    if sys.platform == "win32":
        res = _run_cmd(["netsh", "wlan", "show", "interfaces"])
        profile = ""
        ssid = ""
        for line in res.stdout.splitlines():
            # Matches Profile / Perfil / Profil across localized Windows builds
            mp = re.match(r"^\s*(?:Profile|Perfil|Profil| All User Profile)\s*:\s*(.+?)\s*$", line, re.IGNORECASE)
            if mp and mp.group(1):
                profile = mp.group(1)
            ms = re.match(r"^\s*SSID\s*:\s*(.+?)\s*$", line)
            if ms and ms.group(1):
                ssid = ms.group(1)
        return profile or ssid
    if sys.platform.startswith("linux"):
        res = _run_cmd(["nmcli", "-t", "-f", "NAME,TYPE", "con", "show", "--active"])
        for line in res.stdout.splitlines():
            if "wireless" in line or "802-11-wireless" in line:
                return line.split(":")[0]
    return ""


def _build_windows_wlan_xml(ssid: str, password: str) -> str:
    esc_ssid = saxutils.escape(ssid)
    esc_pwd = saxutils.escape(password)
    hex_ssid = ssid.encode("utf-8").hex().upper()
    return f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{esc_ssid}</name>
    <SSIDConfig>
        <SSID>
            <hex>{hex_ssid}</hex>
            <name>{esc_ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>manual</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{esc_pwd}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""


def _linux_join_with_passwd_file(ssid: str, password: str) -> bool:
    """Join via a NetworkManager profile whose key is passed in a private temp file, never in argv."""
    _run_cmd(["nmcli", "con", "delete", "id", ssid], 15.0)
    add = _run_cmd([
        "nmcli", "con", "add", "type", "wifi", "con-name", ssid, "ssid", ssid,
        "connection.autoconnect", "no",
        "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk-flags", "2",  # 2 = key not stored in the profile
        "ipv4.never-default", "yes", "ipv6.method", "disabled",
    ], 20.0)
    if add.returncode != 0:
        return False
    fd, path = tempfile.mkstemp(prefix="openpin-psk-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:  # mkstemp creates it 0600
            fh.write(f"802-11-wireless-security.psk:{password}\n")
        up = _run_cmd(["nmcli", "con", "up", "id", ssid, "passwd-file", path], 45.0)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if up.returncode != 0:
        _run_cmd(["nmcli", "con", "delete", "id", ssid], 15.0)
        return False
    return True


async def connect_to_pin_hotspot(ssid: str, password: str) -> None:
    for _ in range(10):
        visible = await asyncio.to_thread(scan_visible_ssids)
        if ssid in visible:
            break
        await asyncio.sleep(2.5)

    if sys.platform == "win32":
        xml_body = _build_windows_wlan_xml(ssid, password)
        fd, xml_path = tempfile.mkstemp(prefix="openpin-wlan-", suffix=".xml")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(xml_body)
            add_res = await asyncio.to_thread(_run_cmd, ["netsh", "wlan", "add", "profile", f"filename={xml_path}", "user=current"])
            if add_res.returncode != 0:
                raise WifiSyncError("Windows rejected temporary Wi-Fi profile creation.")
        finally:
            try:
                os.unlink(xml_path)
            except OSError:
                pass

        con_res = await asyncio.to_thread(_run_cmd, ["netsh", "wlan", "connect", f"name={ssid}", f"ssid={ssid}"])
        if con_res.returncode != 0:
            raise WifiSyncError(f"Could not trigger Windows Wi-Fi connection to '{ssid}'. Make sure Wi-Fi is turned ON.")
        return

    if sys.platform.startswith("linux"):
        if await asyncio.to_thread(_linux_join_with_passwd_file, ssid, password):
            return
        # Fallback for older NetworkManager builds: password goes on the command line.
        res = await asyncio.to_thread(_run_cmd, ["nmcli", "dev", "wifi", "connect", ssid, "password", password], 45.0)
        if res.returncode != 0:
            raise WifiSyncError(f"Failed to join device Wi-Fi '{ssid}' via NetworkManager.")
        await asyncio.to_thread(_run_cmd, ["nmcli", "con", "mod", ssid, "ipv4.never-default", "yes", "ipv6.method", "disabled"])
        return

    raise WifiSyncError("Automatic Wi-Fi switching is supported on Windows and Linux. On macOS, join the device Wi-Fi manually or use Bluetooth mode.")


async def restore_home_wifi(pin_ssid: str, previous_profile: str) -> None:
    if sys.platform == "win32":
        if pin_ssid:
            await asyncio.to_thread(_run_cmd, ["netsh", "wlan", "disconnect"])
            await asyncio.to_thread(_run_cmd, ["netsh", "wlan", "delete", "profile", f"name={pin_ssid}"])
        if previous_profile and previous_profile != pin_ssid:
            await asyncio.to_thread(_run_cmd, ["netsh", "wlan", "connect", f"name={previous_profile}"])
    elif sys.platform.startswith("linux"):
        if pin_ssid:
            await asyncio.to_thread(_run_cmd, ["nmcli", "con", "down", pin_ssid])
            await asyncio.to_thread(_run_cmd, ["nmcli", "con", "delete", pin_ssid])
        if previous_profile and previous_profile != pin_ssid:
            await asyncio.to_thread(_run_cmd, ["nmcli", "con", "up", previous_profile])


def local_copy_complete(wav_path: Path, device_size_bytes: int) -> bool:
    """A local WAV counts as a safe copy only if its length matches the recording on the device.

    Device audio is 4,000 bytes/s of Opus; the WAV is 32,000 bytes/s of PCM. Allow 2 % slack for
    decoder padding and the trimmed last frame.
    """
    try:
        wav_bytes = wav_path.stat().st_size
    except OSError:
        return False
    if device_size_bytes <= 0:
        return wav_bytes > 44
    wav_seconds = max(0, wav_bytes - 44) / 32000.0
    device_seconds = device_size_bytes / audio.BYTES_PER_SECOND
    return wav_seconds >= device_seconds * 0.98


# ---------------------------------------------------------------------------
# End-to-end Wi-Fi Fast Sync session
# ---------------------------------------------------------------------------

async def run_wifi_session(
    address: str,
    token: str,
    recordings_dir: Path,
    fallback_ssid: str = "",
    fallback_password: str = "",
    download_mode: str | list[int] = "none",  # "none" | "all_new" | list[int]
    existing_ids: set[str] | None = None,
    delete_ids: list[int] | None = None,
    on_event: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    existing = existing_ids or set()
    to_delete = list(delete_ids or [])
    padded_token = token.ljust(32, "0")

    def emit(ev: str, **fields: Any) -> None:
        if on_event:
            on_event({"ev": ev, **fields})

    previous_wifi = await asyncio.to_thread(get_current_wifi_profile)
    home_ips = await asyncio.to_thread(local_ipv4_addresses)
    joined = asyncio.Event()      # set once this PC is on the recorder's own hotspot
    claimed: list[str] = []       # remote IP of the one connection allowed to run the session
    before_ssids = set(await asyncio.to_thread(scan_visible_ssids))

    done_event = asyncio.Event()
    session_result: dict[str, Any] = {
        "device_info": {},
        "recordings": [],
        "saved": [],
        "deleted": [],
    }
    session_error: list[str] = []
    target_ssid = ""

    async def handle_ws(ws: Any) -> None:
        remote_ip = str((ws.remote_address or ("",))[0])
        local_ip = str((ws.local_address or ("",))[0])
        if not joined.is_set() or claimed or not is_device_peer(remote_ip, local_ip, home_ips):
            # Not the recorder (or a second client): never send it the device token.
            await ws.close(code=1008, reason="not expected")
            return
        claimed.append(remote_ip)
        files_map: dict[int, tuple[int, int]] = {}
        queue_dl: list[int] = []
        queue_del: list[int] = list(to_delete)
        current_id: int | None = None
        current_buf = bytearray()
        last_prog = 0.0
        list_count = 0
        got_heartbeat = False
        finished_at: float | None = None

        async def start_next_download() -> bool:
            nonlocal current_id, current_buf
            if not queue_dl:
                return False
            current_id = queue_dl.pop(0)
            size_b, scene = files_map[current_id]
            current_buf = bytearray()
            emit("progress", id=str(current_id), received=0, total=size_b, remaining=len(queue_dl))
            await ws.send(pack_ws_frame(MSG_FILE_SYNC, {"session": current_id, "scene": scene, "start": 0, "end": size_b}))
            return True

        async def start_next_delete() -> bool:
            while queue_del:
                did = queue_del.pop(0)
                if did not in files_map:
                    continue
                # Safety guard: only delete from the recorder if a complete local .wav copy exists.
                if not local_copy_complete(recordings_dir / f"{did}.wav", files_map[did][0]):
                    emit("warn", id=str(did), msg="Skipped deletion: no complete local WAV copy found.")
                    continue
                await ws.send(pack_ws_frame(MSG_FILE_DELETE, {"session": did, "scene": files_map[did][1]}))
                return True
            return False

        async def after_downloads() -> bool:
            if await start_next_delete():
                return True
            if to_delete and list_count == 1:
                await ws.send(pack_ws_frame(MSG_FILE_LIST, {"uid": 0, "start": 0, "single": 0}))
                return True
            return False

        try:
            while True:
                if finished_at is not None and (got_heartbeat or time.monotonic() - finished_at > 8.0):
                    break
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=2.5 if finished_at else 90.0)
                except asyncio.TimeoutError:
                    if finished_at is not None:
                        continue
                    raise WifiSyncError("Device stopped responding during Wi-Fi transfer.")
                except Exception:
                    if finished_at is not None:
                        break
                    raise WifiSyncError("Device disconnected unexpectedly from Wi-Fi transfer.")

                if isinstance(raw, str):
                    continue
                mtype, meta, binary = unpack_ws_frame(raw)
                if finished_at is not None and mtype != MSG_HEARTBEAT:
                    continue

                if mtype == MSG_HELLO:
                    # Privacy critical: NEVER include `sn` (serial number = Wi-Fi password) in logs or events!
                    info_clean = {
                        "firmware": meta.get("version", ""),
                        "protocol": meta.get("pVer"),
                    }
                    session_result["device_info"].update({k: v for k, v in info_clean.items() if v is not None})
                    emit("info", **session_result["device_info"])
                    await ws.send(pack_ws_frame(MSG_HELLO, {"token": padded_token}))
                    await ws.send(pack_ws_frame(MSG_HANDSHAKE, {"token": padded_token, "stamp": int(time.time())}))

                elif mtype == MSG_HANDSHAKE:
                    if meta.get("status") != 0:
                        raise WifiSyncError("Device rejected Wi-Fi handshake.")
                    await ws.send(pack_ws_frame(MSG_FILE_LIST, {"uid": 0, "start": 0, "single": 0}))

                elif mtype == MSG_HEARTBEAT:
                    hb = {k: meta[k] for k in ("charging", "voltage", "battery") if k in meta}
                    session_result["device_info"].update(hb)
                    emit("info", **hb)
                    await ws.send(pack_ws_frame(MSG_HEARTBEAT, {"stamp": int(time.time())}))
                    got_heartbeat = True

                elif mtype == MSG_FILE_LIST:
                    files_map.clear()
                    for idx in range(0, len(binary) - 9, 10):
                        sid, size_b, scene = struct.unpack_from("<IIH", binary, idx)
                        files_map[sid] = (size_b, scene)
                    list_count += 1
                    rec_entries = [
                        {
                            "id": str(sid),
                            "size_bytes": sz,
                            "duration_seconds": round(sz / audio.BYTES_PER_SECOND, 1),
                            "already_saved": str(sid) in existing or (recordings_dir / f"{sid}.wav").exists(),
                        }
                        for sid, (sz, _sc) in sorted(files_map.items(), reverse=True)
                    ]
                    session_result["recordings"] = rec_entries
                    emit("list", recordings=rec_entries)

                    if list_count > 1:
                        finished_at = time.monotonic()
                        continue

                    if download_mode == "all_new":
                        queue_dl = [
                            sid for sid in files_map
                            if str(sid) not in existing and not (recordings_dir / f"{sid}.wav").exists()
                        ]
                    elif isinstance(download_mode, list):
                        queue_dl = [sid for sid in download_mode if sid in files_map]
                    else:
                        queue_dl = []

                    if not await start_next_download() and not await after_downloads():
                        finished_at = time.monotonic()

                elif mtype == MSG_FILE_CONTENT and current_id is not None:
                    current_buf.extend(binary)
                    now_m = time.monotonic()
                    expected_total = files_map[current_id][0]
                    if now_m - last_prog > 0.35:
                        last_prog = now_m
                        emit("progress", id=str(current_id), received=len(current_buf), total=expected_total, remaining=len(queue_dl))

                    if meta.get("last") == 1:
                        raw_bytes = bytes(current_buf)
                        if len(raw_bytes) != expected_total:
                            raise WifiSyncError(f"Incomplete download for {current_id} ({len(raw_bytes)}/{expected_total} bytes).")
                        dest_wav = recordings_dir / f"{current_id}.wav"
                        dur = await asyncio.to_thread(audio.decode_asr_to_wav, raw_bytes, dest_wav)
                        session_result["saved"].append({"id": str(current_id), "filename": dest_wav.name, "duration_seconds": dur})
                        emit("saved", id=str(current_id), filename=dest_wav.name, duration_seconds=dur)
                        current_id = None
                        current_buf = bytearray()
                        if not await start_next_download() and not await after_downloads():
                            finished_at = time.monotonic()

                elif mtype == MSG_FILE_DELETE:
                    del_sid = str(meta.get("session", ""))
                    if meta.get("status") == 0:
                        session_result["deleted"].append(del_sid)
                        emit("deleted", id=del_sid)
                    if not await after_downloads():
                        finished_at = time.monotonic()

                elif mtype in (0, MSG_WIFI_CLOSE):
                    break

            try:
                await ws.send(pack_ws_frame(MSG_WIFI_CLOSE, {}))
            except Exception:
                pass
        except Exception as exc:
            session_error.append(str(exc))
        finally:
            done_event.set()

    try:
        async with serve(handle_ws, "0.0.0.0", WS_PORT, ping_interval=None, max_size=None):
            emit("phase", step="ble_hotspot")
            ble_info = await ble_client.open_wifi_hotspot(address, token)
            session_result["device_info"].update({
                k: v for k, v in ble_info.items() if k not in ("ssid", "password")
            })
            emit("info", **session_result["device_info"])

            ssid = ble_info.get("ssid") or fallback_ssid
            password = ble_info.get("password") or fallback_password

            if not ssid or not password:
                # Wait briefly and detect any newly appeared Wi-Fi network to help the user
                await asyncio.sleep(3.5)
                after_ssids = await asyncio.to_thread(scan_visible_ssids)
                new_candidates = [s for s in after_ssids if s not in before_ssids]
                raise WifiSyncError(
                    "WIFI_CREDENTIALS_NEEDED:" + json.dumps({"candidates": new_candidates})
                )

            target_ssid = ssid
            emit("phase", step="joining_wifi", ssid=ssid)
            await connect_to_pin_hotspot(ssid, password)
            joined.set()
            emit("phase", step="waiting_device")

            timeout_s = 1800.0 if download_mode != "none" else 90.0
            try:
                await asyncio.wait_for(done_event.wait(), timeout=timeout_s)
            except asyncio.TimeoutError:
                raise WifiSyncError(
                    "The recorder did not connect to port 8081 in time. "
                    "On Windows, make sure Python is allowed through Windows Defender Firewall (Private & Public networks)."
                )
            await asyncio.sleep(0.25)
    finally:
        if target_ssid:
            emit("phase", step="restoring_wifi")
            await restore_home_wifi(target_ssid, previous_wifi)

    if session_error:
        raise WifiSyncError(session_error[0])

    emit("done", saved=len(session_result["saved"]), deleted=len(session_result["deleted"]))
    return session_result
