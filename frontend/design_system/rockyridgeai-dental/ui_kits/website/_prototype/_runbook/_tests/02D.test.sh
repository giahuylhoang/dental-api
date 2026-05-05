#!/usr/bin/env bash
# Test for Task 02D — admin-patients.html
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-patients.html"

assert_file_exists "$F"
assert_file_size   "$F" 9000 45000
assert_active_key  "$F" "patients"

assert_contains "$F" "The Roster"
assert_contains "$F" "CRM rollup from agent calls."
assert_contains "$F" "any status"

assert_contains "$F" "ReactDOM.createRoot"
assert_contains "$F" "AdminSidebar"
assert_contains "$F" "../../../colors_and_type.css"
assert_contains "$F" "ADMIN_MOCK"

# Drawer must link to call detail
assert_grep_count "$F" "admin-call-detail\\.html" 1 999

test_summary
