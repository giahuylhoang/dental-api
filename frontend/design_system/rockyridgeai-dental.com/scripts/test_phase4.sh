#!/usr/bin/env bash
# Phase 4 test: seed data files + canonical enum spellings.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
WEB="$ROOT/ui_kits/website"
fail=0

FILES=(leads threads claims lab_cases treatment_plans providers services recalls waitlist denture_cases audit_log tooth_chart users clinics index)

echo "[1] Each seed file exists, parses as JS, exports a window global"
for f in "${FILES[@]}"; do
  p="$DATA/$f.js"
  if [[ ! -s "$p" ]]; then echo "  ✗ MISSING/EMPTY $f.js"; fail=1; continue; fi
  if ! node --check "$p" >/dev/null 2>&1; then echo "  ✗ $f.js has syntax errors"; fail=1; continue; fi
  if [[ "$f" == "index" ]]; then
    echo "  ✓ $f.js (aggregator)"
  else
    if grep -qE "window\.[A-Z_]+" "$p"; then echo "  ✓ $f.js"; else echo "  ✗ $f.js does not set a window global"; fail=1; fi
  fi
done

echo "[2] Canonical enum spellings"
check_enum() {
  # check_enum <file> <field> <pattern>
  if grep -qE "$3" "$1"; then echo "  ✓ $(basename $1) $2 enum"; else echo "  ✗ $(basename $1) $2 enum mismatch"; fail=1; fi
}
[[ -f "$DATA/leads.js" ]]           && check_enum "$DATA/leads.js"           status      'NEW|CONTACTED|QUALIFIED|CONVERTED|LOST'
[[ -f "$DATA/claims.js" ]]          && check_enum "$DATA/claims.js"          status      'draft|submitted|accepted|adjudicated|paid|rejected|partial'
[[ -f "$DATA/lab_cases.js" ]]       && check_enum "$DATA/lab_cases.js"       status      'draft|sent|in_progress|returned|remake|cancelled'
[[ -f "$DATA/treatment_plans.js" ]] && check_enum "$DATA/treatment_plans.js" status      'draft|presented|accepted|in_progress|completed|declined'
[[ -f "$DATA/recalls.js" ]]         && check_enum "$DATA/recalls.js"         status      'pending|sent|completed|cancelled'
[[ -f "$DATA/waitlist.js" ]]        && check_enum "$DATA/waitlist.js"        status      'open|filled|expired|cancelled'
[[ -f "$DATA/denture_cases.js" ]]   && check_enum "$DATA/denture_cases.js"   arch        'upper|lower|both'
[[ -f "$DATA/tooth_chart.js" ]]     && check_enum "$DATA/tooth_chart.js"     status      'present|missing|extracted|implant|bridge_pontic|crowned|filled|root_treated|to_extract'

echo "[3] data/index.js references every other seed file"
if [[ -f "$DATA/index.js" ]]; then
  for f in "${FILES[@]}"; do
    [[ "$f" == "index" ]] && continue
    if grep -q "$f.js" "$DATA/index.js"; then echo "  ✓ index references $f.js"; else echo "  ✗ index missing $f.js"; fail=1; fi
  done
fi

echo "[4] At least one HTML page consumes each new global"
PAIRS=(
  "leads:LEADS"
  "threads:THREADS"
  "claims:CLAIMS"
  "lab_cases:LAB_CASES"
  "treatment_plans:TREATMENT_PLANS"
  "providers:PROVIDERS"
  "services:SERVICES"
  "recalls:RECALLS"
  "waitlist:WAITLIST"
  "denture_cases:DENTURE_CASES"
  "audit_log:AUDIT_LOG"
  "tooth_chart:TOOTH_CHART"
  "users:USERS"
  "clinics:CLINICS"
)
for pair in "${PAIRS[@]}"; do
  k="${pair%%:*}"
  v="${pair##*:}"
  if grep -lqE "window\.${v}\b|\b${v}\b" "$WEB"/*.html 2>/dev/null; then
    echo "  ✓ window.$v consumed by a page"
  elif grep -qE "src=\"[^\"]*data/${k}\.js\"" "$WEB"/*.html 2>/dev/null; then
    echo "  ✓ $k.js loaded via <script src>"
  else
    echo "  ⚠ window.$v not yet consumed by any page (allowed if used in Phase 6 only)"
  fi
done

if [[ $fail -ne 0 ]]; then echo "PHASE 4 FAILED"; exit 1; fi
echo "PHASE 4 PASSED"
