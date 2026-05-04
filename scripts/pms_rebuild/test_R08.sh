#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f "web/app/(app)/crm/page.tsx" || { echo "FAIL: web/app/(app)/crm/page.tsx missing"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS R08"
