#!/usr/bin/env bash
# Test for Task 02A — admin-dashboard.html
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-dashboard.html"

assert_file_exists "$F"
assert_file_size   "$F" 9000 60000
assert_active_key  "$F" "dashboard"

# Verbatim
assert_contains "$F" "The Receptionist"
assert_contains "$F" "Recent calls and transcripts."
assert_contains "$F" "CRM rollup from agent calls."
assert_contains "$F" "Today's appointments (read-only)."
assert_contains "$F" "Hours, holidays, transfer rules."
assert_contains "$F" "Edit the AI greeting message."

# Structural
assert_contains "$F" "ReactDOM.createRoot"
assert_contains "$F" "AdminSidebar"
assert_contains "$F" "../../../colors_and_type.css"
assert_contains "$F" "ADMIN_MOCK"

# No chart library imports
assert_grep_count "$F" "from ['\"]chart" 0 0
assert_grep_count "$F" "recharts|d3-|@nivo|chart\\.js" 0 0

test_summary
