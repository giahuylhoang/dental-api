#!/usr/bin/env bash
# Test for Task 03C — voice & empty-state pass
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

PROT="ui_kits/website/_prototype"
PAGES=(
  "$PROT/admin-dashboard.html"
  "$PROT/admin-calls.html"
  "$PROT/admin-call-detail.html"
  "$PROT/admin-patients.html"
  "$PROT/admin-schedule.html"
  "$PROT/admin-routing.html"
  "$PROT/admin-greeting.html"
)

# Hype-word allow-list across all admin pages
HYPE=(
  "AI-powered"
  "world-class"
  "cutting-edge"
  "seamless"
  "delight"
  "revolutionary"
  "supercharge"
  "unleash"
)
for word in "${HYPE[@]}"; do
  hits=$(grep -F -l -- "$word" "${PAGES[@]}" 2>/dev/null || true)
  if [[ -z "$hits" ]]; then
    ok "no '$word' in admin pages"
  else
    bad "'$word' found in: $hits"
  fi
done

# Empty-state copy contract — at least one page should carry each
declare -a EMPTIES=(
  "The first call your AI takes will land here. Nothing to set up."
  "No calls match these filters. Widen the date range or clear an outcome to see more."
  "No calls yet. The first call we take for you will land here."
  "This call ended before either side spoke. The audio above is the full record."
  "Your patient list builds itself as we take calls. Once a few come in, you'll see them here, with every conversation linked."
  "No patients match. Try clearing a filter."
  "Nothing on the books for this day."
  "No custom greeting persisted yet. The agent uses the YAML default until you save one."
  "Pick a moment and press Preview to see what the agent would do."
)
for e in "${EMPTIES[@]}"; do
  hits=$(grep -F -l -- "$e" "${PAGES[@]}" 2>/dev/null || true)
  if [[ -n "$hits" ]]; then
    ok "empty-state present: ${e:0:60}…"
  else
    bad "empty-state missing: ${e:0:60}…"
  fi
done

test_summary
