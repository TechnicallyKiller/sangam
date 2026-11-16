#!/usr/bin/env bash
# One-command offline demonstration on this prepared laptop.
set -euo pipefail
cd "$(dirname "$0")/.."
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export DATABASE_URL=""
export CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
export SANGAM_DATA_DIR="$PWD/.data/offline"
echo 'Local dashboard: http://127.0.0.1:5173'
echo 'Operator token: SANGAM_ADMIN_TOKEN in the private .env file'
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
task_api_pid=$!
trap 'kill "$task_api_pid" 2>/dev/null || true' EXIT
cd frontend
VITE_API_URL=http://127.0.0.1:8000 npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
