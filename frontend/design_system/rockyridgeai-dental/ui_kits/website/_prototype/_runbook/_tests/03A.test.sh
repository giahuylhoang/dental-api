#!/usr/bin/env bash
# Test for Task 03A — INDEX integration & nav sanity
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

INDEX="ui_kits/website/INDEX.md"
PROT="ui_kits/website/_prototype"

assert_file_exists "$INDEX"
assert_contains "$INDEX" "## AI Receptionist Admin Prototype"
assert_contains "$INDEX" "admin-shell.html"
assert_contains "$INDEX" "admin-dashboard.html"
assert_contains "$INDEX" "admin-calls.html"
assert_contains "$INDEX" "admin-call-detail.html"
assert_contains "$INDEX" "admin-patients.html"
assert_contains "$INDEX" "admin-schedule.html"
assert_contains "$INDEX" "admin-routing.html"
assert_contains "$INDEX" "admin-greeting.html"
assert_contains "$INDEX" "AdminSidebar.jsx"
assert_contains "$INDEX" "admin_mock.js"

# Existing kit sections must still be present (regression check)
assert_contains "$INDEX" "| File | Purpose | Sidebar Key | Data Files | JSX Components |"
assert_contains "$INDEX" "dashboard.html"

# Existing Sidebar.jsx must NOT have admin keys added
KIT_SIDEBAR="ui_kits/website/Sidebar.jsx"
if [[ -f "$KIT_SIDEBAR" ]]; then
  if grep -E -q "(admin-dashboard|admin-calls|admin-call-detail|admin-greeting|admin-routing)" "$KIT_SIDEBAR"; then
    bad "kit Sidebar.jsx was modified (admin entries leaked in)"
  else
    ok "kit Sidebar.jsx untouched"
  fi
fi

# Each admin-* page (that exists) must use the right active=
declare -A KEYS=(
  [admin-dashboard.html]=dashboard
  [admin-calls.html]=calls
  [admin-call-detail.html]=calls
  [admin-patients.html]=patients
  [admin-schedule.html]=schedule
  [admin-routing.html]=routing
  [admin-greeting.html]=greeting
  [admin-shell.html]=dashboard
)
for page in "${!KEYS[@]}"; do
  if [[ -f "$PROT/$page" ]]; then
    assert_active_key "$PROT/$page" "${KEYS[$page]}"
  fi
done

test_summary
