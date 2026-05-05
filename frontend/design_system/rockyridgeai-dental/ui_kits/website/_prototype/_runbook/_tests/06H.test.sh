#!/usr/bin/env bash
# Test for Task 06H — admin-disclosure.html (NEW)
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-disclosure.html"

assert_file_exists "$F"
assert_file_size   "$F" 7000 26000

assert_contains "$F" "AI disclosure"
assert_contains "$F" "When the AI introduces itself"
assert_contains "$F" "When required by law, the AI must say it's not human at the start of every call."
assert_contains "$F" "Disclosure phrase"
assert_contains "$F" "Save disclosure"
assert_contains "$F" "Engineer-managed"
assert_contains "$F" "0 / 280 characters"
assert_contains "$F" "Last reviewed"
assert_contains "$F" "<AdminSidebar"
assert_contains "$F" 'active="disclosure"'
assert_contains "$F" "Rockyridge Dental AI"
assert_grep_count "$F" 'id="rrd-profile-pill"' 1 1
assert_grep_count "$F" '<textarea' 1 3

assert_contains "$F" "data/ai_config.js"
assert_absent  "$F" "world-class"

test_summary
