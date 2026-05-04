#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f "web/app/(app)/communications/page.tsx" || { echo "FAIL: communications/page.tsx"; exit 1; }
test -f "web/app/(app)/crm/page.tsx" || { echo "FAIL: crm/page.tsx"; exit 1; }
grep -q 'LockedFeature' "web/app/(app)/communications/page.tsx" || { echo "FAIL: communications must use LockedFeature for composer"; exit 1; }
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T11"
