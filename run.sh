#!/usr/bin/env sh
# Ensure PORT is set (Railway sets it; default 8000 for local)
export PORT="${PORT:-8000}"
exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
