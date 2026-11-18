"""Clean, watermark-free decoder for raw 80-byte Opus (.asr) streams produced by Plaud devices.

Each recording downloaded over Wi-Fi or Bluetooth consists of consecutive 80-byte raw Opus packets
(20 ms per packet at 32 kbit/s = 4,000 bytes/second). Writing fresh PCM frames via Python's standard
`wave` module produces a standard 16 kHz 16-bit mono WAV file with zero hardware serial metadata.
"""
from __future__ import annotations

import os
import wave
from pathlib import Path

OPUS_PACKET_BYTES = 80
BYTES_PER_SECOND = 4000  # 32 kbit/s raw Opus


class AudioDecodeError(Exception):
    pass


def decode_asr_to_wav(raw_opus: bytes, dest_wav: Path) -> float:
    """Decode raw 80-byte Opus frames into a clean 16 kHz mono PCM WAV file.

    Returns the decoded audio duration in seconds.
    """
    if not raw_opus or len(raw_opus) < OPUS_PACKET_BYTES:
        raise AudioDecodeError("Audio stream is empty or shorter than a single 80-byte Opus frame.")

    try:
        import av
    except ImportError as exc:
        raise AudioDecodeError("PyAV ('av') is required to decode raw Opus streams into WAV.") from exc

    # Trim any trailing incomplete chunk rather than failing an entire recording
    usable_len = (len(raw_opus) // OPUS_PACKET_BYTES) * OPUS_PACKET_BYTES
    decoder = av.CodecContext.create("opus", "r")
    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)

    dest_wav.parent.mkdir(parents=True, exist_ok=True)
    tmp_wav = dest_wav.with_suffix(".wav.tmp")
    total_samples = 0

    try:
        with wave.open(str(tmp_wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            for offset in range(0, usable_len, OPUS_PACKET_BYTES):
                chunk = raw_opus[offset:offset + OPUS_PACKET_BYTES]
                for frame in decoder.decode(av.Packet(chunk)):
                    for out_frame in resampler.resample(frame):
                        pcm = out_frame.to_ndarray().tobytes()
                        total_samples += len(pcm) // 2
                        wf.writeframes(pcm)
            # Flush resampler
            for out_frame in resampler.resample(None):
                pcm = out_frame.to_ndarray().tobytes()
                total_samples += len(pcm) // 2
                wf.writeframes(pcm)

        if os.name != "nt":
            try:
                os.chmod(tmp_wav, 0o600)
            except OSError:
                pass
        os.replace(tmp_wav, dest_wav)
    except Exception:
        try:
            tmp_wav.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    return round(total_samples / 16000.0, 2)


def sanitize_wav_bytes(wav_bytes: bytes) -> bytes:
    """Strip any non-standard RIFF chunks (such as embedded serial watermarks) from an existing WAV."""
    import io
    with wave.open(io.BytesIO(wav_bytes), "rb") as src:
        params = (src.getnchannels(), src.getsampwidth(), src.getframerate())
        pcm = src.readframes(src.getnframes())
    out = io.BytesIO()
    with wave.open(out, "wb") as dst:
        dst.setnchannels(params[0])
        dst.setsampwidth(params[1])
        dst.setframerate(params[2])
        dst.writeframes(pcm)
    return out.getvalue()
