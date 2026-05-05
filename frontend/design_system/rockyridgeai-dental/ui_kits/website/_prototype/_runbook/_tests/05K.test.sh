#!/usr/bin/env bash
# Test for Task 05K — settings.html: AI Knowledge tab
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/settings.html"

assert_file_exists "$F"
assert_file_size   "$F" 18000 90000

# New tab
assert_contains "$F" "'AI Knowledge'"
assert_contains "$F" "The Knowledge base"
assert_contains "$F" "Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions."
assert_contains "$F" "Last updated"
assert_contains "$F" "Word count"
assert_contains "$F" "Save knowledge updates"
assert_contains "$F" "denture_faq.md"
assert_contains "$F" "practice_info.md"
assert_contains "$F" "No knowledge yet. Drop a markdown file in to give the agent something to draw on."

# All 4 AI tabs in TABS array
assert_contains "$F" "'AI Greeting'"
assert_contains "$F" "'AI Routing'"
assert_contains "$F" "'AI Services'"
assert_contains "$F" "'AI Knowledge'"

# Earlier verbatim survives
assert_contains "$F" "Save greeting"
assert_contains "$F" "Save routing"
assert_contains "$F" "Save service catalogue"

# Original 8 tabs still present
for t in 'Clinic info' 'Working hours' 'Operatories' 'Providers' 'Users & roles' 'Integrations' 'Notifications' 'Audit log'; do
  assert_contains "$F" "'$t'"
done

# ai_config.js loaded
assert_grep_count "$F" 'data/ai_config.js' 1 1

test_summary
