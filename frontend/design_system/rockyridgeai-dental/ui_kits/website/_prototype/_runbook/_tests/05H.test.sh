#!/usr/bin/env bash
# Test for Task 05H — settings.html: AI Greeting tab
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/settings.html"

assert_file_exists "$F"
assert_file_size   "$F" 12000 60000

# New tab name in TABS array
assert_contains "$F" "'AI Greeting'"

# New tab body verbatim
assert_contains "$F" "The Greeting"
assert_contains "$F" "Welcome to … How can I help you today?"
assert_contains "$F" "0 / 280 characters"
assert_contains "$F" "No custom greeting persisted yet. The agent uses the YAML default until you save one."
assert_contains "$F" "First-time edits land as pending_review. An engineer (email allow-listed in GREETING_APPROVERS) must call /approve once per clinic; after that, edits auto-approve."
assert_contains "$F" "Approve clinic (engineer-gated)"
assert_contains "$F" "Save greeting"
assert_contains "$F" "Auto-approval enabled"
assert_contains "$F" "Pending review"
assert_contains "$F" "What the AI says when it picks up a call."

# Original 8 tabs still present
assert_contains "$F" "'Clinic info'"
assert_contains "$F" "'Working hours'"
assert_contains "$F" "'Operatories'"
assert_contains "$F" "'Providers'"
assert_contains "$F" "'Users & roles'"
assert_contains "$F" "'Integrations'"
assert_contains "$F" "'Notifications'"
assert_contains "$F" "'Audit log'"

# Original tab body content survives (sample assertions)
assert_contains "$F" 'defaultValue="Oak Dental Calgary"'
assert_contains "$F" "Send SMS + email when appointment is booked"

# Data files loaded
assert_contains "$F" "data/clinics.js"
assert_contains "$F" "data/ai_config.js"

test_summary
