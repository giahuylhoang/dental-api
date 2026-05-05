#!/usr/bin/env bash
# Test for Task 02G — admin-greeting.html
# Run from KIT_ROOT (rockyridgeai-dental.com/).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-greeting.html"

assert_file_exists "$F"
assert_file_size   "$F" 4000 32000
assert_active_key  "$F" "greeting"

# Verbatim copy contract from 02G-greeting.md
assert_contains "$F" "Greeting"
assert_contains "$F" "Welcome to … How can I help you today?"
assert_contains "$F" "/ 280 characters"
assert_contains "$F" "Save greeting"
assert_contains "$F" "Engineer approval"
assert_contains "$F" "pending_review"
assert_contains "$F" "GREETING_APPROVERS"
assert_contains "$F" "/approve"
assert_contains "$F" "Approve clinic (engineer-gated)"
assert_contains "$F" "No custom greeting persisted yet. The agent uses the YAML default until you save one."

# Structural
assert_contains "$F" "ReactDOM.createRoot"
assert_contains "$F" "AdminSidebar"
assert_contains "$F" "../../../colors_and_type.css"

test_summary
