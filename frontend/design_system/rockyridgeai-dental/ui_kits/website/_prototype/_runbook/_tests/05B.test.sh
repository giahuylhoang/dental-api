#!/usr/bin/env bash
# Test for Task 05B — data/clinics.js rewrite
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="data/clinics.js"

assert_file_exists "$F"
assert_file_size   "$F" 600 4000

assert_contains "$F" "northeast-denture-clinic"
assert_contains "$F" "market-mall-denture"
assert_contains "$F" "Northeast Denture Clinic"
assert_contains "$F" "Market Mall Denture Clinic"
assert_contains "$F" "America/Edmonton"
assert_contains "$F" "+15879738089"
assert_contains "$F" "+13682990959"
assert_contains "$F" "5340 Centre St NE"
assert_contains "$F" "3625 Shaganappi Trail NW"
assert_contains "$F" "window.CLINICS"

# Two id: lines exactly
assert_grep_count "$F" "^      id: \"" 2 2

# Old demo seeds gone
assert_absent "$F" "id: \"default\""
assert_absent "$F" "rockyridge-dental"

test_summary
