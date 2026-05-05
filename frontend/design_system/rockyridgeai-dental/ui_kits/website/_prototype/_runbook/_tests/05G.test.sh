#!/usr/bin/env bash
# Test for Task 05G — TopBar.jsx profile dropdown
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/TopBar.jsx"

assert_file_exists "$F"
assert_file_size   "$F" 2000 10000

# Profile menu hooks
assert_contains "$F" "rrd-profile-pill"
assert_contains "$F" "rrd-profile-menu"
assert_contains "$F" 'role="menu"'
assert_contains "$F" 'role="menuitem"'

# Menu items
assert_contains "$F" "Account"
assert_contains "$F" "Sign out"

# Sign-out wires through RRD.logout and login.html
assert_contains "$F" "RRD.logout"
assert_contains "$F" "login.html?logout=1"

# Existing structure preserved
assert_contains "$F" "Object.assign(window, { TopBar })"
assert_contains "$F" "breadcrumb"
assert_contains "$F" "getSession"

# React.useState used (UMD pattern)
assert_contains "$F" "React.useState"

test_summary
