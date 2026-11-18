"""Unit tests verifying OpenPin core modules, privacy masking, log extraction, and frame codecs."""
from __future__ import annotations

import io
import os
import struct
import sys
import tempfile
import unittest
import wave
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openpin import audio, ble_client, btsnoop, store, wifi_sync


def _make_fake_btsnoop(token_hex: str) -> bytes:
    # btsnoop v1 header: "btsnoop\0", version=1, datalink=1002 (H4)
    hdr = b"btsnoop\x00" + struct.pack(">II", 1, 1002)
    att_payload = b"\x52\x25\x00\x01\x01\x00\x02\x00\x00" + token_hex.encode("ascii")
    l2cap = struct.pack("<HH", len(att_payload), 0x0004) + att_payload
    acl = b"\x02" + struct.pack("<HH", 0x0040, len(l2cap)) + l2cap
    rec_hdr = struct.pack(">IIIIq", len(acl), len(acl), 0, 0, 0)
    return hdr + rec_hdr + acl


class OpenPinTests(unittest.TestCase):
    def test_btsnoop_and_zip_extraction(self) -> None:
        sample_tok = "a1b2c3d4e5f60718293a4b5c6d7e8f90"
        snoop_bytes = _make_fake_btsnoop(sample_tok)
        self.assertEqual(btsnoop.extract_tokens_from_upload(snoop_bytes, "btsnoop_hci.log"), [sample_tok])

        # Nested zip inside Android bugreport zip
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z_in:
            z_in.writestr("FS/data/misc/bluetooth/logs/btsnoop_hci.log", snoop_bytes)
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w") as z_out:
            z_out.writestr("bugreport-nested.zip", inner.getvalue())

        extracted = btsnoop.extract_tokens_from_upload(outer.getvalue(), "bugreport.zip")
        self.assertEqual(extracted, [sample_tok])

    def test_ws_frame_roundtrip(self) -> None:
        raw = wifi_sync.pack_ws_frame(wifi_sync.MSG_HANDSHAKE, {"token": "0" * 32, "stamp": 1700000000})
        mtype, meta, tail = wifi_sync.unpack_ws_frame(raw)
        self.assertEqual(mtype, wifi_sync.MSG_HANDSHAKE)
        self.assertEqual(meta["stamp"], 1700000000)
        self.assertEqual(tail, b"")

    def test_public_state_never_leaks_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["OPENPIN_CONFIG_DIR"] = tmp
            fake_state = {
                "device": {"address": "AA:BB:CC:DD:EE:FF", "name": "MyPin", "model": "Plaud NotePin (Realtek)"},
                "token": "0123456789abcdef0123456789abcdef",
                "wifi": {"ssid": "PIN_AP", "password": "SUPER_SECRET_SERIAL"},
            }
            pub = store.public_state(fake_state)
            serialized = repr(pub)
            self.assertNotIn("0123456789abcdef0123456789abcdef", serialized)
            self.assertNotIn("SUPER_SECRET_SERIAL", serialized)
            self.assertEqual(pub["device"]["address_masked"], "AA:BB:••:••:EE:FF")

    def test_wav_sanitizer_strips_extra_chunks(self) -> None:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 160)
        # Append fake trailing metadata chunk containing a fake serial string
        dirty = buf.getvalue() + b"JUNK\x0c\x00\x00\x00SERIAL123456"
        clean = audio.sanitize_wav_bytes(dirty)
        self.assertNotIn(b"SERIAL123456", clean)
        self.assertTrue(clean.startswith(b"RIFF"))

    def test_device_classifier(self) -> None:
        self.assertEqual(ble_client.classify_device("AnyCustomName", [0x005D], []), "Plaud NotePin (Realtek)")
        self.assertEqual(ble_client.classify_device("PLAUD_NOTE", [0x0059], []), "Plaud Note (Nordic)")
        self.assertIsNone(ble_client.classify_device("Headphones", [0x004C], []))

    def test_device_peer_check(self) -> None:
        home = {"192.168.0.10"}
        # Recorder on its own hotspot: new local address, same /24.
        self.assertTrue(wifi_sync.is_device_peer("192.168.43.1", "192.168.43.2", home))
        # A machine on the home LAN (local address is the home one) never gets the token.
        self.assertFalse(wifi_sync.is_device_peer("192.168.0.66", "192.168.0.10", home))
        # Different subnet, loopback and garbage are refused.
        self.assertFalse(wifi_sync.is_device_peer("10.0.0.5", "192.168.43.2", home))
        self.assertFalse(wifi_sync.is_device_peer("127.0.0.1", "127.0.0.1", home))
        self.assertFalse(wifi_sync.is_device_peer("nope", "192.168.43.2", home))
        self.assertTrue(wifi_sync.is_device_peer("::ffff:192.168.43.1", "::ffff:192.168.43.2", home))

    def test_delete_guard_needs_complete_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "1700000000.wav"
            self.assertFalse(wifi_sync.local_copy_complete(wav, 40_000))  # missing
            wav.write_bytes(b"\0" * (44 + 32000 * 5))                      # 5 s of a 10 s recording
            self.assertFalse(wifi_sync.local_copy_complete(wav, 40_000))
            wav.write_bytes(b"\0" * (44 + 32000 * 10))                     # full 10 s
            self.assertTrue(wifi_sync.local_copy_complete(wav, 40_000))


class LocalOnlyGuardTests(unittest.TestCase):
    """The panel must refuse other websites and DNS-rebinding hosts."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
            from openpin import server
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(f"server deps not installed: {exc}")
        cls.tmp = tempfile.TemporaryDirectory()
        store.CONFIG_DIR = Path(cls.tmp.name) / "config"
        store.RECORDINGS_DIR = Path(cls.tmp.name) / "recordings"
        store.STATE_FILE = store.CONFIG_DIR / "state.json"
        cls.client = TestClient(server.app, base_url="http://127.0.0.1:8765")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_local_requests_work(self) -> None:
        self.assertEqual(self.client.get("/api/state").status_code, 200)
        r = self.client.post("/api/reset", headers={"Origin": "http://127.0.0.1:8765", "Sec-Fetch-Site": "same-origin"})
        self.assertEqual(r.status_code, 200)

    def test_rebinding_host_refused(self) -> None:
        r = self.client.get("/api/state", headers={"Host": "evil.example:8765"})
        self.assertEqual(r.status_code, 403)

    def test_cross_site_posts_refused(self) -> None:
        r = self.client.post("/api/reset", headers={"Origin": "https://evil.example"})
        self.assertEqual(r.status_code, 403)
        r = self.client.post("/api/reset", headers={"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(r.status_code, 403)

    def test_upload_cannot_impersonate_or_overwrite_a_recording(self) -> None:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"\x00\x00" * 160)
        files = {"file": ("1700000000.wav", buf.getvalue(), "audio/wav")}
        r = self.client.post("/api/convert-file", files=files)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["filename"], "upload_1700000000.wav")  # numeric ids are reserved
        r = self.client.post("/api/convert-file", files=files)
        self.assertEqual(r.status_code, 409)                              # never overwrites


if __name__ == "__main__":
    unittest.main()
