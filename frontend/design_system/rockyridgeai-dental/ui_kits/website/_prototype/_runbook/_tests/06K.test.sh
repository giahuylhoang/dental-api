#!/usr/bin/env bash
# Test for Task 06K — AdminSidebar.jsx config-group expansion
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/AdminSidebar.jsx"

assert_file_exists "$F"
assert_file_size   "$F" 8000 32000

# All 10 keys (6 existing + 4 new)
for key in dashboard calls patients schedule routing greeting services knowledge disclosure voice; do
  assert_contains "$F" "key: '$key'"
done

# New page hrefs
assert_contains "$F" "admin-services.html"
assert_contains "$F" "admin-knowledge.html"
assert_contains "$F" "admin-disclosure.html"
assert_contains "$F" "admin-voice.html"

# New labels
assert_contains "$F" "'Services'"
assert_contains "$F" "'Knowledge'"
assert_contains "$F" "'AI disclosure'"
assert_contains "$F" "'Voice & persona'"

# v2 clinic switcher preserved
assert_contains "$F" "rrd-clinic-switcher"

# Branding preserved
assert_contains "$F" "DENTAL AI"
assert_absent  "$F" "RECEPTIONIST"

# Existing export preserved
assert_contains "$F" "Object.assign(window, { AdminSidebar })"

test_summary
