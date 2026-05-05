#!/usr/bin/env bash
# Test for Task 05L — login.html copy edit
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/login.html"

assert_file_exists "$F"

# New copy present, old absent
assert_contains "$F" "Sign in to your workspace"
assert_absent  "$F" "Sign in to your clinic"

# Brand wordmark untouched
assert_contains "$F" "ROCKYRIDGE"
assert_contains "$F" "DENTAL AI"

test_summary
