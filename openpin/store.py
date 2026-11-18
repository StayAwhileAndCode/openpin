"""Local configuration and recording storage.

All sensitive credentials (device auth token, optional Wi-Fi hotspot password/serial) stay strictly
inside `<project>/config/state.json` (gitignored, mode 0600 on POSIX) and are NEVER returned in clear
text to the UI or written to logs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path(os.environ.get("OPENPIN_CONFIG_DIR", ROOT_DIR / "config"))
RECORDINGS_DIR = Path(os.environ.get("OPENPIN_RECORDINGS_DIR", ROOT_DIR / "recordings"))
STATE_FILE = CONFIG_DIR / "state.json"

HEX_TOKEN_RE = re.compile(r"^[0-9a-fA-F]{16,64}$")
MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def ensure_dirs() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        try:
            os.chmod(CONFIG_DIR, 0o700)
            os.chmod(RECORDINGS_DIR, 0o700)
        except OSError:
            pass


def validate_token(raw: str) -> str:
    cleaned = raw.strip()
    if not HEX_TOKEN_RE.match(cleaned) or len(cleaned) not in (16, 32):
        raise ValueError("Token must be 16 or 32 hexadecimal characters (0-9, a-f).")
    return cleaned


def token_fingerprint(token: str) -> str:
    if not token:
        return ""
    return hashlib.sha256(token.encode("ascii")).hexdigest()[:16]


def mask_mac(address: str) -> str:
    if not address:
        return ""
    parts = address.split(":")
    if len(parts) == 6:
        return f"{parts[0]}:{parts[1]}:••:••:{parts[4]}:{parts[5]}"
    return address[:4] + "••••"


def load_state() -> dict[str, Any]:
    ensure_dirs()
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(updates: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    state = load_state()
    state.update(updates)
    fd, tmp_path = tempfile.mkstemp(dir=CONFIG_DIR, prefix=".state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
        if os.name != "nt":
            try:
                os.chmod(tmp_path, 0o600)
            except OSError:
                pass
        os.replace(tmp_path, STATE_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return state


def public_state(state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Safe view of local state for the browser UI — never exposes raw token or Wi-Fi password."""
    st = state if state is not None else load_state()
    dev = st.get("device") or {}
    token = st.get("token") or ""
    wifi = st.get("wifi") or {}
    return {
        "device": {
            "address": dev.get("address", ""),
            "address_masked": mask_mac(dev.get("address", "")),
            "name": dev.get("name", ""),
            "model": dev.get("model", ""),
            "company_id": dev.get("company_id"),
            "has_adv_profile": bool(dev.get("manufacturer_hex")),
        } if dev.get("address") else None,
        "has_token": bool(token),
        "token_verified": bool(st.get("token_verified")),
        "token_fingerprint": token_fingerprint(token) if token else "",
        "wifi_configured": bool(wifi.get("ssid") and wifi.get("password")),
        "wifi_ssid": wifi.get("ssid", ""),
        "last_status": st.get("last_status"),
        "recordings_dir": str(RECORDINGS_DIR),
    }


def list_local_recordings() -> list[dict[str, Any]]:
    ensure_dirs()
    items: list[dict[str, Any]] = []
    for wav in sorted(RECORDINGS_DIR.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True):
        st = wav.stat()
        rec_id = wav.stem
        started_iso = ""
        if rec_id.isdigit():
            ts = int(rec_id)
            if 1_577_836_800 <= ts <= 4_102_444_800:  # 2020..2100 sanity window
                started_iso = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().isoformat(timespec="seconds")
        # 16 kHz * 2 bytes (16-bit mono) = 32,000 bytes/sec (+44-byte WAV header)
        duration_s = max(0.0, (st.st_size - 44) / 32000.0)
        items.append({
            "id": rec_id,
            "filename": wav.name,
            "size_bytes": st.st_size,
            "duration_seconds": round(duration_s, 1),
            "started_at": started_iso,
            "saved_at": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
        })
    return items
