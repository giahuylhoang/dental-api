#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -d web || { echo "FAIL: web/ missing"; exit 1; }
test -f web/package.json || { echo "FAIL: web/package.json missing"; exit 1; }
test -f web/next.config.mjs || { echo "FAIL: web/next.config.mjs missing"; exit 1; }
test -f web/.env.local || { echo "FAIL: web/.env.local missing"; exit 1; }
grep -q 'NEXT_PUBLIC_API_URL' web/.env.local || { echo "FAIL: NEXT_PUBLIC_API_URL not in .env.local"; exit 1; }
grep -q 'NEXT_PUBLIC_USE_MSW' web/.env.local || { echo "FAIL: NEXT_PUBLIC_USE_MSW not in .env.local"; exit 1; }
node -e "const p=require('./web/package.json'); for (const d of ['@tanstack/react-query','zustand','@fullcalendar/react','@tiptap/react','@react-pdf/renderer','cmdk','msw']) if (!p.dependencies[d] && !p.devDependencies?.[d]) { console.error('missing dep', d); process.exit(1)}" \
  || { echo "FAIL: required dep missing"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T01"
