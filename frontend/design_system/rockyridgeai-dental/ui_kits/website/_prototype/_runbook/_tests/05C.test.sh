#!/usr/bin/env bash
# Test for Task 05C — data/users.js rewrite
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="data/users.js"

assert_file_exists "$F"
assert_file_size   "$F" 600 4000

assert_contains "$F" "Gia Huy"
assert_contains "$F" "giahuy.l.hoang@gmail.com"
assert_contains "$F" "Owner"
assert_contains "$F" "Front-desk"
assert_contains "$F" "assigned_clinic_ids"
assert_contains "$F" "northeast-denture-clinic"
assert_contains "$F" "market-mall-denture"
assert_contains "$F" "Northeast Front Desk"
assert_contains "$F" "Market Mall Front Desk"
assert_contains "$F" "window.USERS"

# Three users with assigned_clinic_ids
assert_grep_count "$F" "assigned_clinic_ids:" 3 3

# Old demo email gone
assert_absent "$F" "demo@rockyridge.dental"
assert_absent "$F" "clinic_id: \"default\""

test_summary
