#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "[+] Killing any existing uvicorn..."
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

echo "[+] Activating venv and starting AMARS backend..."
source .venv/bin/activate
exec .venv/bin/python -m uvicorn main:app \
  --host 0.0.0.0 --port 8000 --workers 1 \
  --reload \
  --log-level info
