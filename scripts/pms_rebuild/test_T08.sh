#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f "web/app/(app)/patients/page.tsx" || { echo "FAIL: patients/page.tsx"; exit 1; }
test -f "web/app/(app)/patients/[id]/page.tsx" || { echo "FAIL: patients/[id]/page.tsx"; exit 1; }
hex=$(grep -RInE '#[0-9A-Fa-f]{3,8}\b' "web/app/(app)/patients" 2>/dev/null || true)
if [[ -n "$hex" ]]; then echo "FAIL: raw hex"; echo "$hex"; exit 1; fi
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T08"
