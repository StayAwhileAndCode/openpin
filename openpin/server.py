"""Local-only FastAPI server powering the OpenPin browser wizard (binds to 127.0.0.1)."""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from urllib.parse import urlsplit

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import audio, ble_client, btsnoop, store, wifi_sync

STATIC_DIR = Path(__file__).resolve().parent / "static"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")

app = FastAPI(title="OpenPin Local Interface", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Hostnames this panel answers to. Anything else is refused, which blocks DNS-rebinding pages that
# point their own domain at 127.0.0.1 to read recordings or drive the recorder.
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"} | {
    h.strip().lower() for h in os.environ.get("OPENPIN_EXTRA_HOSTS", "").split(",") if h.strip()
}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _hostname(value: str) -> str:
    """Hostname from a Host header or URL netloc, without port; handles [::1]:8765."""
    value = value.strip().lower()
    if value.startswith("["):
        return value[1:value.find("]")] if "]" in value else value
    return value.rsplit(":", 1)[0] if value.count(":") == 1 else value


@app.middleware("http")
async def local_only_guard(request: Request, call_next: Any) -> Any:
    """Only this computer's own browser tab may use the panel.

    - Host must be a local name (stops DNS rebinding).
    - State-changing requests must come from this same panel: a foreign Origin or a cross-site
      Sec-Fetch-Site is refused (stops other websites from posting forms/uploads to 127.0.0.1).
    """
    if _hostname(request.headers.get("host", "")) not in ALLOWED_HOSTS:
        return JSONResponse({"detail": "Forbidden host."}, status_code=403)
    if request.method not in SAFE_METHODS:
        origin = request.headers.get("origin")
        if origin is not None and _hostname(urlsplit(origin).netloc) not in ALLOWED_HOSTS:
            return JSONResponse({"detail": "Cross-origin request refused."}, status_code=403)
        site = request.headers.get("sec-fetch-site")
        if site is not None and site not in ("same-origin", "none"):
            return JSONResponse({"detail": "Cross-site request refused."}, status_code=403)
    return await call_next(request)

# In-memory live status of active BLE / Wi-Fi transfer job
_job_lock = asyncio.Lock()
_job_state: dict[str, Any] = {
    "running": False,
    "mode": "",
    "phase": "idle",
    "current_id": "",
    "received": 0,
    "total": 0,
    "remaining": 0,
    "error": "",
    "wifi_needed": None,
    "device_recordings": [],
    "updated_at": 0.0,
}


def _update_job(**kwargs: Any) -> None:
    _job_state.update(kwargs)
    _job_state["updated_at"] = time.time()


class SelectDeviceReq(BaseModel):
    address: str
    name: str = ""
    model: str = ""
    company_id: int | None = None
    manufacturer_hex: str = ""


class SaveTokenReq(BaseModel):
    token: str
    verify_now: bool = True


class SaveWifiReq(BaseModel):
    ssid: str
    password: str


class WifiSyncReq(BaseModel):
    action: str = "all_new"  # "list" | "all_new" | "selected" | "delete"
    ids: list[str] = []


class BleSyncReq(BaseModel):
    download_ids: list[str] = []


@app.get("/", response_class=HTMLResponse)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/state")
async def api_state() -> dict[str, Any]:
    return {
        "config": store.public_state(),
        "local_recordings": store.list_local_recordings(),
        "job": _job_state,
        "platform": sys.platform,
    }


@app.get("/api/sync/progress")
async def api_sync_progress() -> dict[str, Any]:
    return {
        "job": _job_state,
        "config": store.public_state(),
        "local_recordings": store.list_local_recordings(),
    }


@app.post("/api/scan")
async def api_scan(include_all: bool = False) -> dict[str, Any]:
    try:
        devices = await ble_client.scan_devices(timeout=5.5, include_all=include_all)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Bluetooth scan failed ({type(exc).__name__}). Make sure Bluetooth is enabled on this computer.",
        ) from exc
    for d in devices:
        d["address_masked"] = store.mask_mac(d["address"])
    return {"devices": devices}


@app.post("/api/device/select")
async def api_select_device(req: SelectDeviceReq) -> dict[str, Any]:
    addr = req.address.strip()
    if not addr:
        raise HTTPException(status_code=400, detail="Device address is required.")
    st = store.save_state({
        "device": {
            "address": addr,
            "name": req.name.strip(),
            "model": req.model.strip(),
            "company_id": req.company_id,
            "manufacturer_hex": req.manufacturer_hex.strip(),
        }
    })
    return {"ok": True, "config": store.public_state(st)}


@app.post("/api/token/save")
async def api_save_token(req: SaveTokenReq) -> dict[str, Any]:
    try:
        token = store.validate_token(req.token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    st = store.load_state()
    dev = st.get("device") or {}
    verified = False
    telemetry: dict[str, Any] = {}

    if req.verify_now and dev.get("address"):
        try:
            telemetry = await ble_client.verify_and_read_status(dev["address"], token)
            verified = True
        except ble_client.BlePinError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    updates: dict[str, Any] = {"token": token, "token_verified": verified or bool(st.get("token_verified"))}
    if telemetry:
        prev_status = dict(st.get("last_status") or {})
        prev_status.update(telemetry)
        updates["last_status"] = prev_status

    new_st = store.save_state(updates)
    return {"ok": True, "verified": verified, "telemetry": telemetry, "config": store.public_state(new_st)}


@app.post("/api/token/verify")
async def api_verify_saved_token() -> dict[str, Any]:
    st = store.load_state()
    dev = st.get("device") or {}
    token = st.get("token") or ""
    if not dev.get("address") or not token:
        raise HTTPException(status_code=400, detail="Select a device and configure your key first.")
    try:
        telemetry = await ble_client.verify_and_read_status(dev["address"], token)
    except ble_client.BlePinError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    prev_status = dict(st.get("last_status") or {})
    prev_status.update(telemetry)
    new_st = store.save_state({"token_verified": True, "last_status": prev_status})
    return {"ok": True, "telemetry": telemetry, "config": store.public_state(new_st)}


@app.post("/api/token/extract-log")
async def api_extract_log(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    if len(raw) > 300 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 300 MB safety limit.")
    try:
        candidates = await asyncio.to_thread(btsnoop.extract_tokens_from_upload, raw, file.filename or "")
    except btsnoop.LogExtractError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not candidates:
        raise HTTPException(
            status_code=404,
            detail="No authentication frame found in this file. Make sure HCI snoop logging was enabled BEFORE opening the phone app and letting it connect to your recorder.",
        )

    chosen = candidates[-1]  # Most recent session token
    new_st = store.save_state({"token": chosen, "token_verified": False})
    return {
        "ok": True,
        "candidates_found": len(candidates),
        "token_fingerprint": store.token_fingerprint(chosen),
        "config": store.public_state(new_st),
    }


@app.post("/api/wifi/save")
async def api_save_wifi(req: SaveWifiReq) -> dict[str, Any]:
    ssid = req.ssid.strip()
    pwd = req.password.strip()
    if not ssid or len(pwd) < 8:
        raise HTTPException(status_code=400, detail="Enter the recorder's Wi-Fi SSID and password (serial number, 8+ chars).")
    new_st = store.save_state({"wifi": {"ssid": ssid, "password": pwd}})
    return {"ok": True, "config": store.public_state(new_st)}


@app.post("/api/sync/wifi")
async def api_start_wifi_sync(req: WifiSyncReq) -> dict[str, Any]:
    if _job_state["running"]:
        raise HTTPException(status_code=409, detail="Another sync session is already running.")

    st = store.load_state()
    dev = st.get("device") or {}
    token = st.get("token") or ""
    wifi_cfg = st.get("wifi") or {}
    if not dev.get("address") or not token:
        raise HTTPException(status_code=400, detail="Complete Steps 1 and 2 (device + key) first.")

    dl_mode: str | list[int] = "none"
    del_ids: list[int] = []
    if req.action == "all_new":
        dl_mode = "all_new"
    elif req.action == "selected":
        dl_mode = [int(x) for x in req.ids if x.isdigit()]
    elif req.action == "delete":
        del_ids = [int(x) for x in req.ids if x.isdigit()]

    existing_ids = {r["id"] for r in store.list_local_recordings()}

    async def _runner() -> None:
        async with _job_lock:
            _update_job(
                running=True,
                mode="wifi",
                phase="starting",
                current_id="",
                received=0,
                total=0,
                remaining=0,
                error="",
                wifi_needed=None,
            )

            def on_ev(ev: dict[str, Any]) -> None:
                kind = ev.get("ev")
                if kind == "phase":
                    _update_job(phase=ev.get("step", ""))
                elif kind == "info":
                    cur = dict(store.load_state().get("last_status") or {})
                    cur.update({k: v for k, v in ev.items() if k != "ev"})
                    store.save_state({"last_status": cur, "token_verified": True})
                elif kind == "list":
                    _update_job(phase="listed", device_recordings=ev.get("recordings", []))
                elif kind == "progress":
                    _update_job(
                        phase="downloading",
                        current_id=ev.get("id", ""),
                        received=ev.get("received", 0),
                        total=ev.get("total", 0),
                        remaining=ev.get("remaining", 0),
                    )
                elif kind == "done":
                    _update_job(phase="done")

            try:
                res = await wifi_sync.run_wifi_session(
                    address=dev["address"],
                    token=token,
                    recordings_dir=store.RECORDINGS_DIR,
                    fallback_ssid=wifi_cfg.get("ssid", ""),
                    fallback_password=wifi_cfg.get("password", ""),
                    download_mode=dl_mode,
                    existing_ids=existing_ids,
                    delete_ids=del_ids,
                    on_event=on_ev,
                )
                _update_job(running=False, phase="done", device_recordings=res.get("recordings", []))
            except Exception as exc:
                msg = str(exc)
                if msg.startswith("WIFI_CREDENTIALS_NEEDED:"):
                    payload = json.loads(msg.split(":", 1)[1])
                    _update_job(
                        running=False,
                        phase="wifi_needed",
                        wifi_needed=payload,
                        error="",
                    )
                else:
                    _update_job(running=False, phase="error", error=msg)

    asyncio.create_task(_runner())
    return {"ok": True}


@app.post("/api/sync/ble")
async def api_start_ble_sync(req: BleSyncReq) -> dict[str, Any]:
    if _job_state["running"]:
        raise HTTPException(status_code=409, detail="Another sync session is already running.")

    st = store.load_state()
    dev = st.get("device") or {}
    token = st.get("token") or ""
    if not dev.get("address") or not token:
        raise HTTPException(status_code=400, detail="Complete Steps 1 and 2 (device + key) first.")

    dl_ids = [int(x) for x in req.download_ids if x.isdigit()]

    async def _runner() -> None:
        async with _job_lock:
            _update_job(
                running=True,
                mode="ble",
                phase="connecting_ble",
                current_id="",
                received=0,
                total=0,
                remaining=0,
                error="",
                wifi_needed=None,
            )

            def on_ev(ev: dict[str, Any]) -> None:
                kind = ev.get("ev")
                if kind == "info":
                    cur = dict(store.load_state().get("last_status") or {})
                    cur.update({k: v for k, v in ev.items() if k != "ev"})
                    store.save_state({"last_status": cur, "token_verified": True})
                elif kind == "list":
                    recs = [
                        {
                            "id": r["id"],
                            "size_bytes": r["size_bytes"],
                            "duration_seconds": round(r["size_bytes"] / audio.BYTES_PER_SECOND, 1),
                            "already_saved": (store.RECORDINGS_DIR / f"{r['id']}.wav").exists(),
                        }
                        for r in ev.get("recordings", [])
                    ]
                    _update_job(phase="listed", device_recordings=recs)
                elif kind == "progress":
                    _update_job(
                        phase="downloading",
                        current_id=ev.get("id", ""),
                        received=ev.get("received", 0),
                        total=ev.get("total", 0),
                    )

            try:
                res = await ble_client.ble_list_and_download(
                    address=dev["address"],
                    token=token,
                    download_ids=dl_ids,
                    on_progress=on_ev,
                )
                for rid, raw_opus in res["downloaded"].items():
                    dest = store.RECORDINGS_DIR / f"{rid}.wav"
                    await asyncio.to_thread(audio.decode_asr_to_wav, raw_opus, dest)
                _update_job(running=False, phase="done")
            except Exception as exc:
                _update_job(running=False, phase="error", error=str(exc))

    asyncio.create_task(_runner())
    return {"ok": True}


@app.post("/api/convert-file")
async def api_convert_file(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")
    orig_stem = Path(file.filename or f"converted-{int(time.time())}").stem
    safe_stem = re.sub(r"[^A-Za-z0-9_-]", "_", orig_stem)[:60] or f"audio_{int(time.time())}"
    # Purely numeric names are reserved for recordings downloaded from the device (their id), so an
    # uploaded file can never stand in for a real recording (the delete-from-device guard relies on it).
    if safe_stem.isdigit():
        safe_stem = f"upload_{safe_stem}"
    store.ensure_dirs()
    dest = store.RECORDINGS_DIR / f"{safe_stem}.wav"
    if dest.exists():
        raise HTTPException(status_code=409, detail=f"A file named {dest.name} already exists. Rename the upload and try again.")

    try:
        if raw[:4] == b"RIFF":
            clean_wav = await asyncio.to_thread(audio.sanitize_wav_bytes, raw)
            dest.write_bytes(clean_wav)
        else:
            await asyncio.to_thread(audio.decode_asr_to_wav, raw, dest)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not convert file: {exc}") from exc

    return {"ok": True, "filename": dest.name, "local_recordings": store.list_local_recordings()}


@app.get("/api/recordings/{rec_id}/wav")
async def api_get_wav(rec_id: str, download: bool = False) -> FileResponse:
    if not SAFE_ID_RE.match(rec_id):
        raise HTTPException(status_code=400, detail="Invalid recording identifier.")
    wav_path = store.RECORDINGS_DIR / f"{rec_id}.wav"
    if not wav_path.exists():
        raise HTTPException(status_code=404, detail="Recording not found.")
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{wav_path.name}"'
    return FileResponse(wav_path, media_type="audio/wav", headers=headers)


@app.delete("/api/recordings/{rec_id}")
async def api_delete_local_wav(rec_id: str) -> dict[str, Any]:
    if not SAFE_ID_RE.match(rec_id):
        raise HTTPException(status_code=400, detail="Invalid recording identifier.")
    wav_path = store.RECORDINGS_DIR / f"{rec_id}.wav"
    if wav_path.exists():
        wav_path.unlink()
    return {"ok": True, "local_recordings": store.list_local_recordings()}


@app.post("/api/open-folder")
async def api_open_folder() -> dict[str, Any]:
    store.ensure_dirs()
    folder = str(store.RECORDINGS_DIR)
    try:
        if sys.platform == "win32":
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not open folder automatically: {exc}") from exc
    return {"ok": True, "path": folder}


@app.post("/api/reset")
async def api_reset() -> dict[str, Any]:
    if store.STATE_FILE.exists():
        store.STATE_FILE.unlink()
    _update_job(device_recordings=[], wifi_needed=None, error="", phase="idle")
    return {"ok": True, "config": store.public_state()}
