#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f "web/app/(app)/dashboard/page.tsx" || { echo "FAIL: dashboard/page.tsx missing"; exit 1; }
hex=$(grep -RInE '#[0-9A-Fa-f]{3,8}\b' "web/app/(app)/dashboard" 2>/dev/null || true)
if [[ -n "$hex" ]]; then echo "FAIL: raw hex"; echo "$hex"; exit 1; fi
inline=$(grep -RIn 'style={{' "web/app/(app)/dashboard" 2>/dev/null || true)
if [[ -n "$inline" ]]; then echo "FAIL: inline styles"; echo "$inline"; exit 1; fi
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T07"
