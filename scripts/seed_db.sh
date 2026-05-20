#!/bin/bash
set -e

# Resolve repo root from this script's location so the script works
# regardless of CWD or absolute-path drift across machines.
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

CONNECTION_NAME=$(cat /tmp/conn_name)
APP_PASSWORD=$(cat /tmp/app_pwd)
TOKEN=$(gcloud auth print-access-token)

# Resolve cloud-sql-proxy: prefer PATH (gcloud components install),
# fall back to a repo-root copy for backwards compatibility.
if command -v cloud-sql-proxy >/dev/null 2>&1; then
  PROXY_BIN="cloud-sql-proxy"
elif [ -x "./cloud-sql-proxy" ]; then
  PROXY_BIN="./cloud-sql-proxy"
else
  echo "ERROR: cloud-sql-proxy not found. Install via:" >&2
  echo "  gcloud components install cloud-sql-proxy" >&2
  exit 1
fi

echo "Starting cloud-sql-proxy via $PROXY_BIN..."
"$PROXY_BIN" "$CONNECTION_NAME" --port=5433 --token "$TOKEN" &
PROXY_PID=$!

echo "Waiting for proxy to start..."
sleep 5

echo "Running sync_db.py..."
export DATABASE_URL="postgresql://dentalapp:${APP_PASSWORD}@127.0.0.1:5433/dental_clinic"
uv run python scripts/sync_db.py

echo "Killing proxy..."
kill $PROXY_PID
echo "Done."
