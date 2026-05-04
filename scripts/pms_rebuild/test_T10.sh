#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f "web/app/(app)/lab/page.tsx" || { echo "FAIL: lab/page.tsx"; exit 1; }
test -f "web/app/(app)/billing/page.tsx" || { echo "FAIL: billing/page.tsx"; exit 1; }
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T10"
