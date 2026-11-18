"""Zero-disk-footprint token extractor for Bluetooth HCI captures and phone bugreports.

Supports:
- Android `btsnoop_hci.log` / `.cfa` files (walks HCI H4 ACL -> L2CAP ATT Write packets)
- Android Bug Report `.zip` archives (including nested `.zip` archives, processed purely in RAM)
- Apple iOS PacketLogger `.pklg` / Wireshark `.pcap` / `.pcapng` captures (via frame & prefix scan)
"""
from __future__ import annotations

import io
import re
import struct
import zipfile

BTSNOOP_MAGIC = b"btsnoop\x00"
AUTH_FRAME_PREFIX = b"\x01\x01\x00\x02\x00\x00"
# Matches AUTH_FRAME_PREFIX followed by 32 or 16 ASCII hex bytes (32 checked first)
RAW_AUTH_RE = re.compile(b"\x01\x01\x00\x02\x00\x00([0-9a-fA-F]{32}|[0-9a-fA-F]{16})(?![0-9a-fA-F])")


class LogExtractError(Exception):
    pass


def _extract_from_btsnoop(buf: bytes) -> list[str]:
    """Walk standard btsnoop v1 records and inspect ATT Write Request (0x12) / Write Command (0x52)."""
    if len(buf) < 16 or buf[:8] != BTSNOOP_MAGIC:
        return []
    version, _datalink = struct.unpack_from(">II", buf, 8)
    if version != 1:
        return []

    found: list[str] = []
    offset = 16
    n = len(buf)
    while offset + 24 <= n:
        _orig_len, incl_len = struct.unpack_from(">II", buf, offset)
        pkt_start = offset + 24
        pkt_end = pkt_start + incl_len
        if pkt_end > n:
            break
        pkt = buf[pkt_start:pkt_end]
        offset = pkt_end

        # H4 ACL packet (0x02) or unprefixed ACL depending on datalink (1001 vs 1002)
        for acl in (pkt[1:] if pkt[:1] == b"\x02" else b"", pkt):
            if len(acl) < 8:
                continue
            acl_len = struct.unpack_from("<H", acl, 2)[0]
            l2cap = acl[4:4 + acl_len]
            if len(l2cap) < 4:
                continue
            pdu_len, cid = struct.unpack_from("<HH", l2cap, 0)
            if cid != 0x0004:  # ATT channel
                continue
            att = l2cap[4:4 + pdu_len]
            if len(att) < 3 or att[0] not in (0x52, 0x12):  # Write Command / Write Request
                continue
            value = att[3:]  # skip opcode (1B) + attribute handle (2B LE)
            if value.startswith(AUTH_FRAME_PREFIX):
                candidate = value[len(AUTH_FRAME_PREFIX):]
                try:
                    text = candidate.decode("ascii")
                except UnicodeDecodeError:
                    continue
                if len(text) in (16, 32) and all(c in "0123456789abcdefABCDEF" for c in text):
                    if text not in found:
                        found.append(text)
    return found


def _extract_from_bytes(buf: bytes) -> list[str]:
    tokens = _extract_from_btsnoop(buf)
    for match in RAW_AUTH_RE.finditer(buf):
        tok = match.group(1).decode("ascii")
        if tok not in tokens:
            tokens.append(tok)
    return tokens


def extract_tokens_from_upload(data: bytes, filename: str = "", _depth: int = 0) -> list[str]:
    """Extract all candidate Plaud auth tokens from an uploaded log or `.zip` bugreport in memory."""
    if not data:
        raise LogExtractError("Uploaded file is empty.")

    tokens: list[str] = []

    if _depth < 2 and (filename.lower().endswith(".zip") or data[:4] == b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                # Prioritize Bluetooth snoop logs inside Android bugreports
                names = sorted(
                    zf.namelist(),
                    key=lambda s: (
                        0 if ("btsnoop" in s.lower() or "hci" in s.lower() or s.lower().endswith(".pklg")) else
                        1 if s.lower().endswith(".zip") else 2
                    ),
                )
                for name in names:
                    lower = name.lower()
                    if lower.endswith("/"):
                        continue
                    # Inspect bluetooth logs, nested zips, or bugreport text dumps
                    if any(k in lower for k in ("btsnoop", "hci", "bluetooth", ".pklg", ".cfa", ".log", ".pcap", ".zip")):
                        info = zf.getinfo(name)
                        if info.file_size > 250 * 1024 * 1024:
                            continue
                        content = zf.read(name)
                        for tok in extract_tokens_from_upload(content, name, _depth=_depth + 1):
                            if tok not in tokens:
                                tokens.append(tok)
                        if tokens:
                            return tokens
        except zipfile.BadZipFile:
            pass

    for tok in _extract_from_bytes(data):
        if tok not in tokens:
            tokens.append(tok)

    return tokens
