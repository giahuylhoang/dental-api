#!/usr/bin/env bash
# Test for Task 05J — settings.html: AI Services tab
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/settings.html"

assert_file_exists "$F"
assert_file_size   "$F" 16000 80000

# New tab
assert_contains "$F" "'AI Services'"
assert_contains "$F" "The Service catalogue"
assert_contains "$F" "Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only."

# Column headers + statuses
assert_contains "$F" "Service ID"
assert_contains "$F" "Duration"
assert_contains "$F" "Base price"
assert_contains "$F" "AI Bookable"
assert_contains "$F" "Front-desk only"
assert_contains "$F" "Save service catalogue"
assert_contains "$F" "SVC-001"

# Services data loaded
assert_grep_count "$F" 'data/services.js' 1 1

# Earlier tabs survive
assert_contains "$F" "'AI Greeting'"
assert_contains "$F" "'AI Routing'"
assert_contains "$F" "Save greeting"
assert_contains "$F" "Save routing"

# Original 8 tabs still present
for t in 'Clinic info' 'Working hours' 'Operatories' 'Providers' 'Users & roles' 'Integrations' 'Notifications' 'Audit log'; do
  assert_contains "$F" "'$t'"
done

test_summary
