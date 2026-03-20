#!/usr/bin/env bash
# Run API locally with SQLite (no Supabase/network required).
# Use a different port if 8000 is already in use.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PORT="${PORT:-8001}"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./dental_clinic.db}"

if [[ "$DATABASE_URL" == sqlite* ]]; then
  echo "Syncing local SQLite DB: ./dental_clinic.db (creates/seeds if missing)"
  uv run python scripts/sync_db.py
fi

echo "Starting API on port $PORT with $DATABASE_URL"
exec uv run python run_api.py
