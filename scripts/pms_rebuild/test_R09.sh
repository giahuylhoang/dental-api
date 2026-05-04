#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f "web/app/(app)/reports/page.tsx" || { echo "FAIL: web/app/(app)/reports/page.tsx missing"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS R09"
