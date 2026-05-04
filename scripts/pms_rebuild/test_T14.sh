#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
( cd web && npm run lint ) || { echo "FAIL: lint"; exit 1; }
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
hex=$(grep -RInE '#[0-9A-Fa-f]{3,8}\b' web/app web/components web/lib 2>/dev/null | grep -v design-tokens.css || true)
if [[ -n "$hex" ]]; then echo "FAIL: raw hex"; echo "$hex"; exit 1; fi
inline=$(grep -RIn 'style={{' web/app web/components 2>/dev/null | grep -v node_modules | grep -vE 'Pdf|@react-pdf' || true)
if [[ -n "$inline" ]]; then echo "FAIL: inline styles"; echo "$inline"; exit 1; fi
test -f web/playwright.config.ts || { echo "FAIL: playwright.config.ts"; exit 1; }
test -f web/e2e/smoke.spec.ts || { echo "FAIL: smoke.spec.ts"; exit 1; }
( cd web && npx playwright install --with-deps chromium && npx playwright test ) || { echo "FAIL: playwright"; exit 1; }
echo "PASS T14"
