#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
for f in web/lib/api/client.ts web/lib/auth/store.ts web/lib/auth/auth.ts web/lib/auth/guard.tsx web/lib/query/client.ts web/lib/mocks/browser.ts web/lib/api/v2/types.ts web/app/providers.tsx web/public/mockServiceWorker.js; do
  test -f "$f" || { echo "FAIL: missing $f"; exit 1; }
done
grep -q 'NEXT_PUBLIC_API_URL' web/lib/api/client.ts || { echo "FAIL: client.ts must use NEXT_PUBLIC_API_URL"; exit 1; }
grep -q 'use client' web/lib/auth/store.ts || { echo "FAIL: auth/store.ts missing 'use client'"; exit 1; }
grep -q 'typeof window' web/lib/auth/store.ts || { echo "FAIL: auth/store.ts missing window guard"; exit 1; }
grep -q '<Providers>' web/app/layout.tsx || grep -q 'Providers' web/app/layout.tsx || { echo "FAIL: Providers not used in app/layout.tsx"; exit 1; }
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T04"
