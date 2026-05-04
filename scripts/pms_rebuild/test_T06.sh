#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
need=(
  web/components/layout/AppShell.tsx
  web/components/layout/DynamicCalendar.tsx
  web/app/\(portal\)/layout.tsx
  web/app/\(portal\)/login/page.tsx
  web/app/\(app\)/layout.tsx
  web/app/page.tsx
  web/app/not-found.tsx
)
for f in "${need[@]}"; do
  eval "test -f \"$f\"" || { echo "FAIL: missing $f"; exit 1; }
done
for r in dashboard patients schedule lab billing communications crm plans reports settings; do
  test -f "web/app/(app)/$r/page.tsx" || { echo "FAIL: missing route /$r"; exit 1; }
done
test -f "web/app/(app)/patients/[id]/page.tsx" || { echo "FAIL: missing /patients/[id]"; exit 1; }
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T06"
