#!/usr/bin/env bash
# Test for Task 02B — admin-calls.html
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-calls.html"

assert_file_exists "$F"
assert_file_size   "$F" 9000 45000
assert_active_key  "$F" "calls"

assert_contains "$F" "The Call Log"
assert_contains "$F" "Recent calls and transcripts."

assert_contains "$F" "ReactDOM.createRoot"
assert_contains "$F" "AdminSidebar"
assert_contains "$F" "../../../colors_and_type.css"
assert_contains "$F" "ADMIN_MOCK"

# Booked rows must link with a call_id query param
assert_grep_count "$F" "admin-call-detail\\.html\\?call_id=" 1 999

test_summary
