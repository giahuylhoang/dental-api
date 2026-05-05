#!/usr/bin/env bash
# Test for Task 06D — AdminSidebar.jsx clinic switcher
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/AdminSidebar.jsx"

assert_file_exists "$F"
assert_file_size   "$F" 6000 24000

# Switcher hooks
assert_contains "$F" "rrd-clinic-switcher"
assert_contains "$F" "rrd-clinic-switcher-menu"
assert_contains "$F" "aria-expanded"
assert_contains "$F" "data-clinic-id"
assert_contains "$F" "setCurrentClinic"
assert_contains "$F" "getCurrentClinicId"
assert_contains "$F" "getAssignedClinicIds"
assert_contains "$F" "window.CLINICS"

# Existing structure preserved
assert_contains "$F" "Object.assign(window, { AdminSidebar })"
assert_contains "$F" "const ADMIN_NAV ="
for key in dashboard calls patients schedule routing greeting; do
  assert_contains "$F" "key: '$key'"
done

# Branding from 06B preserved
assert_contains "$F" "DENTAL AI"
assert_absent  "$F" "RECEPTIONIST"
assert_absent  "$F" "Receptionist"

# UMD hooks pattern
assert_contains "$F" "React.useState"

test_summary
