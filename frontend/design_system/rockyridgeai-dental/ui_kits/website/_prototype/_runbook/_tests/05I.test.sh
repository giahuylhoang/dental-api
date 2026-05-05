#!/usr/bin/env bash
# Test for Task 05I — settings.html: AI Routing tab
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/settings.html"

assert_file_exists "$F"
assert_file_size   "$F" 14000 70000

# New tab
assert_contains "$F" "'AI Routing'"
assert_contains "$F" "The Routing"

# Verbatim copy
assert_contains "$F" "Ring timeout (seconds)"
assert_contains "$F" "Front desk numbers (comma-separated, E.164)"
assert_contains "$F" "Backup number (optional)"
assert_contains "$F" "AI SIP URI (read-only here; engineer-managed)"
assert_contains "$F" "Engineer-managed"
assert_contains "$F" "Hours per weekday"
assert_contains "$F" "Both blank means closed that day."
assert_contains "$F" "Holidays (YYYY-MM-DD, one per line)"
assert_contains "$F" "AI handles after-hours calls"
assert_contains "$F" "AI handles in-hours overflow"
assert_contains "$F" "Save routing"
assert_contains "$F" "What would the agent do at a given moment, against the currently saved rules? (Save first if you want to preview a draft.)"
assert_contains "$F" "Preview decision"
assert_contains "$F" "Assume AI healthy"

# AI Greeting (from 05H) still present
assert_contains "$F" "'AI Greeting'"
assert_contains "$F" "Save greeting"

# Original 8 tabs still present
for t in 'Clinic info' 'Working hours' 'Operatories' 'Providers' 'Users & roles' 'Integrations' 'Notifications' 'Audit log'; do
  assert_contains "$F" "'$t'"
done

test_summary
