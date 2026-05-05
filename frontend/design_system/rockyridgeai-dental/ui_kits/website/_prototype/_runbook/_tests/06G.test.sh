#!/usr/bin/env bash
# Test for Task 06G — admin-knowledge.html (NEW)
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-knowledge.html"

assert_file_exists "$F"
assert_file_size   "$F" 8000 32000

assert_contains "$F" "Knowledge"
assert_contains "$F" "The Knowledge base"
assert_contains "$F" "Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions."
assert_contains "$F" "Last updated"
assert_contains "$F" "Word count"
assert_contains "$F" "Save knowledge updates"
assert_contains "$F" "denture_faq.md"
assert_contains "$F" "practice_info.md"
assert_contains "$F" "No knowledge yet. Drop a markdown file in to give the agent something to draw on."
assert_contains "$F" "<AdminSidebar"
assert_contains "$F" 'active="knowledge"'
assert_contains "$F" "Rockyridge Dental AI"
assert_grep_count "$F" 'id="rrd-profile-pill"' 1 1
assert_grep_count "$F" '<textarea' 1 8

assert_contains "$F" "data/ai_config.js"
assert_absent  "$F" "world-class"

test_summary
