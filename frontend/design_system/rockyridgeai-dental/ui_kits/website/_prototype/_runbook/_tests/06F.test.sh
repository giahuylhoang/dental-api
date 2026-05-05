#!/usr/bin/env bash
# Test for Task 06F — admin-services.html (NEW)
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/admin-services.html"

assert_file_exists "$F"
assert_file_size   "$F" 9000 36000

assert_contains "$F" "Services"
assert_contains "$F" "The Service catalogue"
assert_contains "$F" "Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only."
assert_contains "$F" "Service ID"
assert_contains "$F" "Duration"
assert_contains "$F" "Base price"
assert_contains "$F" "AI Bookable"
assert_contains "$F" "Front-desk only"
assert_contains "$F" "Save service catalogue"
assert_contains "$F" "SVC-001"
assert_contains "$F" "<AdminSidebar"
assert_contains "$F" 'active="services"'
assert_contains "$F" "Rockyridge Dental AI"
assert_grep_count "$F" 'id="rrd-profile-pill"' 1 1

# Data scripts loaded
assert_contains "$F" "data/ai_config.js"
assert_contains "$F" "data/services.js"

# No emoji / no hype words
assert_absent "$F" "world-class"
assert_absent "$F" "AI-powered"
assert_absent "$F" "seamless"

test_summary
