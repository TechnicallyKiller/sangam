#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
if [ ! -x .venv/bin/python ]; then
  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -r backend/requirements.txt
fi
echo 'Sangam API: http://127.0.0.1:8000/docs'
echo 'Run npm run dev in frontend/ for the dashboard at http://localhost:5173'
exec .venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
