#!/usr/bin/env bash
# Test for Task 06E — topbar profile dropdown across 8 admin-*.html files
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

PROT="ui_kits/website/_prototype"
PAGES=(
  "$PROT/admin-shell.html"
  "$PROT/admin-dashboard.html"
  "$PROT/admin-calls.html"
  "$PROT/admin-call-detail.html"
  "$PROT/admin-patients.html"
  "$PROT/admin-schedule.html"
  "$PROT/admin-routing.html"
  "$PROT/admin-greeting.html"
)

for p in "${PAGES[@]}"; do
  assert_file_exists "$p"
  # OwnerPill markup hooks
  assert_grep_count "$p" 'id="rrd-profile-pill"' 1 1
  assert_grep_count "$p" 'id="rrd-profile-menu"' 1 1
  assert_contains   "$p" 'role="menu"'
  assert_contains   "$p" 'role="menuitem"'
  assert_contains   "$p" 'Account'
  assert_contains   "$p" 'Sign out'
  assert_contains   "$p" 'RRD.logout'
  assert_contains   "$p" 'login.html?logout=1'
  assert_contains   "$p" 'OwnerPill'
  # Hard-coded DC initials must be gone
  assert_grep_count "$p" '>DC<' 0 0
done

test_summary
