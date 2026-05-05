#!/usr/bin/env bash
# Test for Task 06A — INVENTORY-v4.md
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/INVENTORY-v4.md"

assert_file_exists "$F"
assert_file_size   "$F" 5000 25000

assert_contains "$F" "Plan v3"
assert_contains "$F" "_prototype"
assert_contains "$F" "Dental AI"
assert_contains "$F" "northeast-denture-clinic"
assert_contains "$F" "market-mall-denture"
assert_contains "$F" "admin-services.html"
assert_contains "$F" "admin-knowledge.html"
assert_contains "$F" "admin-disclosure.html"
assert_contains "$F" "admin-voice.html"
assert_contains "$F" "Kit cross-link"
assert_contains "$F" "AI Receptionist"
assert_contains "$F" "dental-api"
assert_contains "$F" "dental-agent"
assert_contains "$F" "rrd-clinic-switcher"
assert_contains "$F" "rrd-profile-pill"
assert_contains "$F" "Phase 0 v4"

assert_grep_count "$F" "^# " 1 12

test_summary
