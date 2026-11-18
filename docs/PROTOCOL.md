# OpenPin Interoperability Protocol Notes

This document summarizes the over-the-air Bluetooth Low Energy (BLE) and local Wi-Fi transfer framing used by Plaud NotePin (Realtek `0x005d`) and Plaud Note (Nordic `0x0059`) voice recorders so owners can access their own recordings locally without cloud services.

---

## 1. BLE Discovery & GATT Characteristics

| Item | Value |
| --- | --- |
| Primary Vendor Service | `00001910-0000-1000-8000-00805f9b34fb` |
| Write Characteristic (Host → Device) | `00002bb1-0000-1000-8000-00805f9b34fb` (Write Without Response) |
| Notify Characteristic (Device → Host) | `00002bb0-0000-1000-8000-00805f9b34fb` (Notify) |
| Battery Level Characteristic | `00002a19-0000-1000-8000-00805f9b34fb` (Standard BLE Battery Service) |
| Manufacturer ID — Plaud Note | `0x0059` (Nordic Semiconductor) |
| Manufacturer ID — Plaud NotePin | `0x005d` (Realtek Semiconductor) |

> **Single-connection rule:** The recorder accepts one BLE central connection at a time. Disconnect or disable Bluetooth on your phone briefly before connecting from a computer.

---

## 2. BLE Control & Bulk Framing

All vendor BLE commands written to `0x2bb1` use a 3-byte header:

```text
01 <opcode: u16 LE> <payload...>
```

### Key Control Opcodes

- **`0x0001` — Authenticate:**
  - Request: `01 01 00 02 00 00 <16 or 32 ASCII hex token bytes>`
  - Response on `0x2bb0`: `01 01 00 <status: u8> ...` (`0x00` = accepted, `0x01` = rejected).
- **`0x0003` — Device State:** nullary (`01 03 00`).
- **`0x0004` — Sync Real-Time Clock:**
  - Request: `01 04 00 <unix_epoch: u32 LE> <tz_hours: i8> <tz_minutes: u8>`
- **`0x0006` — Storage Capacity:** nullary (`01 06 00`), returns free/total storage counters.
- **`0x000A` — Activate Local Wi-Fi Transfer AP:**
  - Request: `01 0a 00`
  - Optional response payload: `<status: u8> <ssid_len: u8> <ssid_utf8> <pass_len: u8> <pass_utf8>`. On firmware builds that return an empty string, the WPA2 password defaults to the device's factory Serial Number.
- **`0x001A` — Delta File List (BLE):**
  - Request: `01 1a 00 <epoch: u32 LE> <session_id: u32 LE> <single: u8>`
- **`0x001C` — Read File Chunk (BLE Bulk Stream):**
  - Request: `01 1c 00 <file_id: u32 LE> <offset: u32 LE> <length: u32 LE>`
  - Triggers bulk notifications starting with `0x02`:
    ```text
    02 <file_id: u32 LE> <offset: u32 LE> <chunk_len: u8> <raw_opus_bytes...>
    ```
  - Stream ends when `<offset>` equals `0xFFFFFFFF`.

---

## 3. Local Wi-Fi Fast Transfer (WebSocket Port `8081`)

Once opcode `0x000A` activates the recorder's temporary WPA2-Personal access point and the computer joins that AP, the recorder connects as a WebSocket client to `<host_ip>:8081`.

Each binary WebSocket message uses an 8-byte header followed by UTF-8 JSON and optional binary audio data:

```text
<total_len: u24 LE> <version: u8 = 1> <msg_type: u16 LE> <json_len: u16 LE> <json_bytes> <binary_tail>
```

| `msg_type` | Direction | Purpose |
| --- | --- | --- |
| `2` (`HELLO`) | Device ↔ Host | Exchanges 32-char zero-padded `token` and firmware version |
| `1` (`HANDSHAKE`) | Host ↔ Device | Sends `{"token": "...", "stamp": <epoch>}`; device replies `{"status": 0}` |
| `3` (`HEARTBEAT`) | Device ↔ Host | Reports `charging` / `voltage`; host echoes `{"stamp": <epoch>}` |
| `11` (`FILE_LIST`) | Host ↔ Device | Host sends `{"uid":0,"start":0,"single":0}`; binary tail carries 10-byte records `<session_id: u32 LE, size_bytes: u32 LE, scene: u16 LE>` |
| `12` (`FILE_SYNC`) | Host → Device | Requests `<session, scene, start, end>` |
| `13` (`FILE_CONTENT`) | Device → Host | Streams binary audio chunks until JSON metadata contains `"last": 1` |
| `14` (`FILE_DELETE`) | Host ↔ Device | Deletes `<session, scene>` from recorder flash |
| `4` (`WIFI_CLOSE`) | Host → Device | Cleanly shuts down the recorder's Wi-Fi AP |

---

## 4. Raw Opus Audio Format (`.asr`)

Both Wi-Fi and BLE transfers deliver raw 32 kbit/s Opus frames:
- Fixed packet size: **80 bytes** per 20 ms frame (`4,000 bytes/second`).
- Decoding consecutive 80-byte packets through standard libopus (`PyAV`) and writing fresh PCM samples (`16 kHz`, `16-bit`, `mono`) yields clean `.wav` files with zero embedded hardware serial identifiers.
