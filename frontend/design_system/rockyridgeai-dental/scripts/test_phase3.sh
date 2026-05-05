#!/usr/bin/env bash
# Phase 3 test: shared component extraction.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$ROOT/ui_kits/website"
fail=0

COMPS=(StatusPill DataTable Drawer Tabs FormField Breadcrumb MoneyCell MonoText IconButton SearchInput FilterChips KanbanBoard CalendarGrid Avatar ChartCard)

echo "[1] Each component file exists and is non-empty"
for c in "${COMPS[@]}"; do
  f="$WEB/$c.jsx"
  if [[ -s "$f" ]]; then echo "  ✓ $c.jsx"; else echo "  ✗ MISSING/EMPTY $c.jsx"; fail=1; fi
done

echo "[2] Each component exposes a window global"
for c in "${COMPS[@]}"; do
  f="$WEB/$c.jsx"
  [[ ! -f "$f" ]] && continue
  if grep -qE "(window\.${c}|Object\.assign\s*\(\s*window\s*,\s*\{[^}]*${c}\b)" "$f"; then
    echo "  ✓ window.$c"
  else
    echo "  ✗ $c.jsx does not expose window.$c"; fail=1
  fi
done

echo "[3] StatusPill is referenced by ≥ 4 pages (proves it replaced inline pills)"
n=$(grep -lE '<StatusPill\b' "$WEB"/*.html 2>/dev/null | wc -l | tr -d ' ')
if [[ "$n" -ge 4 ]]; then echo "  ✓ StatusPill used in $n pages"; else echo "  ✗ StatusPill used in only $n pages (expected ≥4)"; fail=1; fi

echo "[4] Each component file is referenced by at least one HTML page (no orphans)"
for c in "${COMPS[@]}"; do
  if grep -qE "src=\"[^\"]*${c}\.jsx\"" "$WEB"/*.html 2>/dev/null; then
    echo "  ✓ $c.jsx is loaded"
  else
    echo "  ✗ $c.jsx is orphaned (no <script src> reference)"; fail=1
  fi
done

if [[ $fail -ne 0 ]]; then echo "PHASE 3 FAILED"; exit 1; fi
echo "PHASE 3 PASSED"
