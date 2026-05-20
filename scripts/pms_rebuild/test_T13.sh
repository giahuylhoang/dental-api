#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f "web/app/(app)/reports/page.tsx" || { echo "FAIL: reports/page.tsx"; exit 1; }
test -f "web/app/(app)/plans/page.tsx" || { echo "FAIL: plans/page.tsx"; exit 1; }
grep -q 'LockedFeature' "web/app/(app)/reports/page.tsx" || { echo "FAIL: reports needs LockedFeature for advanced panel"; exit 1; }
grep -q 'LockedFeature' "web/app/(app)/plans/page.tsx" || { echo "FAIL: plans must be entirely LockedFeature"; exit 1; }
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T13"
