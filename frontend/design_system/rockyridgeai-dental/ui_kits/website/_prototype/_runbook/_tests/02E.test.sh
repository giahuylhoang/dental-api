#!/usr/bin/env bash
# Test for Task 02E — admin-schedule.html
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-schedule.html"

assert_file_exists "$F"
assert_file_size   "$F" 7000 35000
assert_active_key  "$F" "schedule"

assert_contains "$F" "The Schedule"
assert_contains "$F" "Today's appointments (read-only)."

assert_contains "$F" "ReactDOM.createRoot"
assert_contains "$F" "AdminSidebar"
assert_contains "$F" "../../../colors_and_type.css"
assert_contains "$F" "ADMIN_MOCK"

# AI-booked appointments link back to call detail
assert_grep_count "$F" "admin-call-detail\\.html" 1 999

# Read-only — no create/new affordance
assert_grep_count "$F" "(\\+ New|Add appointment|Create appointment)" 0 0

test_summary
