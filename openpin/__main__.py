"""Entrypoint: starts the local-only OpenPin web interface and opens the user's browser."""
from __future__ import annotations

import argparse
import os
import threading
import time
import webbrowser

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenPin — Local Offline Sync for Plaud NotePin & Note")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1 — local only)")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        # The panel refuses unknown Host headers; let the address the user chose through.
        os.environ["OPENPIN_EXTRA_HOSTS"] = args.host
        print("[!] Warning: the panel has no login. Only bind to a non-local address on a network you trust.")

    url = f"http://{args.host}:{args.port}"
    if not args.no_browser and args.host in ("127.0.0.1", "localhost"):
        def _open() -> None:
            time.sleep(1.1)
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run("openpin.server:app", host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
