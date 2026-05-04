#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
required=(badge button card command data-table dialog dropdown-menu input page-header popover scroll-area select separator sheet skeleton sonner switch tabs textarea toast toaster tooltip)
for f in "${required[@]}"; do
  test -f "web/components/ui/${f}.tsx" || { echo "FAIL: missing web/components/ui/${f}.tsx"; exit 1; }
done
test -f web/lib/utils.ts || { echo "FAIL: web/lib/utils.ts missing"; exit 1; }
grep -q 'export function cn' web/lib/utils.ts || { echo "FAIL: cn() not exported"; exit 1; }
hex=$(grep -RInE '#[0-9A-Fa-f]{3,8}\b' web/components/ui 2>/dev/null || true)
if [[ -n "$hex" ]]; then echo "FAIL: raw hex in components/ui"; echo "$hex"; exit 1; fi
inline=$(grep -RIn 'style={{' web/components/ui 2>/dev/null || true)
if [[ -n "$inline" ]]; then echo "FAIL: inline styles in components/ui"; echo "$inline"; exit 1; fi
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T03"
