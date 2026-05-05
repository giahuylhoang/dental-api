#!/usr/bin/env bash
# Test for Task 02C — admin-call-detail.html
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-call-detail.html"

assert_file_exists "$F"
assert_file_size   "$F" 16000 80000
assert_active_key  "$F" "calls"

assert_contains "$F" "Under the hood"

assert_contains "$F" "ReactDOM.createRoot"
assert_contains "$F" "AdminSidebar"
assert_contains "$F" "../../../colors_and_type.css"
assert_contains "$F" "ADMIN_MOCK"
assert_contains "$F" "RRD.query"

# Call-not-found path
assert_contains "$F" "Call not found"

test_summary
