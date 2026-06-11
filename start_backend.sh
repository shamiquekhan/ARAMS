#!/bin/bash
cd /home/shamique/projects/arams/backend
export PYTHONPATH=/home/shamique/projects/arams/backend
exec /home/shamique/projects/arams/backend/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
