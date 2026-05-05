#!/usr/bin/env bash
# Test for Task 05E — lib/auth.js extension
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="lib/auth.js"

assert_file_exists "$F"
assert_file_size   "$F" 1500 6000

# New helpers
assert_contains "$F" "setCurrentClinic"
assert_contains "$F" "getCurrentClinicId"
assert_contains "$F" "getAssignedClinicIds"
assert_contains "$F" "clinic-changed"

# Login carries assigned_clinic_ids into session
assert_contains "$F" "assigned_clinic_ids"

# Existing functions still present
assert_contains "$F" "RRD.getSession"
assert_contains "$F" "RRD.login"
assert_contains "$F" "RRD.logout"
assert_contains "$F" "RRD.requireSession"

# IIFE preserved
assert_grep_count "$F" "^\\(function" 1 1

# Storage key unchanged
assert_contains "$F" "'rrd_session'"

test_summary
