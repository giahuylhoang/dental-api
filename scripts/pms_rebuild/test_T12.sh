#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f "web/app/(app)/settings/page.tsx" || { echo "FAIL: settings/page.tsx"; exit 1; }
locked=$(grep -c 'LockedFeature' "web/app/(app)/settings/page.tsx" || true)
if [[ "${locked:-0}" -lt 2 ]]; then echo "FAIL: settings must contain at least 2 LockedFeature usages (got $locked)"; exit 1; fi
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T12"
