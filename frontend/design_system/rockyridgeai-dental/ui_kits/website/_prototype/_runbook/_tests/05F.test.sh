#!/usr/bin/env bash
# Test for Task 05F — Sidebar.jsx clinic switcher
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/Sidebar.jsx"

assert_file_exists "$F"
assert_file_size   "$F" 4000 18000

# Switcher hooks
assert_contains "$F" "rrd-clinic-switcher"
assert_contains "$F" "rrd-clinic-switcher-menu"
assert_contains "$F" "aria-expanded"
assert_contains "$F" "data-clinic-id"

# State helpers it depends on
assert_contains "$F" "setCurrentClinic"
assert_contains "$F" "getCurrentClinicId"
assert_contains "$F" "getAssignedClinicIds"
assert_contains "$F" "window.CLINICS"

# Existing structure preserved
assert_contains "$F" "Object.assign(window, { Sidebar })"
assert_contains "$F" "const NAV ="

# Original nav keys still present
for key in dashboard patients schedule plans lab billing comms crm reports settings; do
  assert_contains "$F" "key: '$key'"
done

# React.useState used (UMD pattern)
assert_contains "$F" "React.useState"

test_summary
