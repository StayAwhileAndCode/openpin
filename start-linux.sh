#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "============================================================"
echo "  OpenPin — Local Offline Sync for Plaud NotePin & Note"
echo "  Your hardware, your audio — 100% local, no cloud"
echo "============================================================"
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "[!] Python 3 not found / Python 3 não encontrado."
    echo "    Install python3 and python3-venv (e.g. sudo apt install python3 python3-venv)"
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "[1/2] Creating isolated virtual environment (.venv)..."
    python3 -m venv .venv
    echo "[2/2] Installing dependencies..."
    .venv/bin/python -m pip install --upgrade pip >/dev/null
    .venv/bin/python -m pip install -r requirements.txt
fi

echo "[OK] Starting local panel on http://127.0.0.1:8765 ..."
exec .venv/bin/python -m openpin "$@"
