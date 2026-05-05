#!/usr/bin/env bash
# Test for Task 06I — admin-voice.html (NEW)
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-voice.html"

assert_file_exists "$F"
assert_file_size   "$F" 8000 28000

assert_contains "$F" "Voice & persona"
assert_contains "$F" "What the AI calls itself, what it calls your providers, and what it asks for first."
assert_contains "$F" "Assistant name"
assert_contains "$F" "Provider title"
assert_contains "$F" "Reason question"
assert_contains "$F" "Language"
assert_contains "$F" "Save voice"
assert_contains "$F" "Hear it back"
assert_contains "$F" "Denturist"
assert_contains "$F" "What brings you in?"
assert_contains "$F" "<AdminSidebar"
assert_contains "$F" 'active="voice"'
assert_contains "$F" "Rockyridge Dental AI"
assert_grep_count "$F" 'id="rrd-profile-pill"' 1 1
assert_grep_count "$F" '<select' 2 4

assert_contains "$F" "data/ai_config.js"
assert_absent  "$F" "world-class"

test_summary
