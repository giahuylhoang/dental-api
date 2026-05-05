#!/usr/bin/env bash
# Test for Task 06J — kit Sidebar.jsx cross-link
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/Sidebar.jsx"

assert_file_exists "$F"
assert_file_size   "$F" 6000 24000

# New nav item
assert_contains "$F" "ai-receptionist"
assert_contains "$F" "AI Receptionist"
assert_contains "$F" "_prototype/admin-dashboard.html"
assert_contains "$F" "relogin=1"
assert_contains "$F" "isNew"
assert_contains "$F" "NEW"
assert_contains "$F" "RRD.logout"
assert_contains "$F" "login.html?next="

# All 10 original keys still present
for key in dashboard patients schedule plans lab billing comms crm reports settings; do
  assert_contains "$F" "key: '$key'"
done

# Existing structure preserved
assert_contains "$F" "Object.assign(window, { Sidebar })"
assert_contains "$F" "const NAV ="

# v2 clinic switcher (added in 05F) still present
assert_contains "$F" "rrd-clinic-switcher"

test_summary
