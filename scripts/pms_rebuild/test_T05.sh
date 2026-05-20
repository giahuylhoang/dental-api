#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
needed=(AppointmentCard Avatar Breadcrumb CalendarGrid ChartCard CTA DataTable Drawer EmptyState FilterChips FormField Hero IconButton KanbanBoard KpiTile LabPipeline LoginCard MoneyCell MonoText Nav PatientCard Philosophy Pillars SearchInput Sidebar StatusPill Tabs ToothChartTile TopBar LockedFeature)
for c in "${needed[@]}"; do
  test -f "web/components/dental/${c}.tsx" || { echo "FAIL: missing dental/${c}.tsx"; exit 1; }
done
inline=$(grep -RIn 'style={{' web/components/dental 2>/dev/null || true)
if [[ -n "$inline" ]]; then echo "FAIL: inline styles in dental:"; echo "$inline"; exit 1; fi
hex=$(grep -RInE '#[0-9A-Fa-f]{3,8}\b' web/components/dental 2>/dev/null || true)
if [[ -n "$hex" ]]; then echo "FAIL: raw hex in dental:"; echo "$hex"; exit 1; fi
( cd web && npx tsc --noEmit ) || { echo "FAIL: tsc"; exit 1; }
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T05"
