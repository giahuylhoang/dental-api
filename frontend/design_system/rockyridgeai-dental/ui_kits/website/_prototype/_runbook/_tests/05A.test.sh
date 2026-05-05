#!/usr/bin/env bash
# Test for Task 05A — INVENTORY-v3.md
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="ui_kits/website/_prototype/INVENTORY-v3.md"

assert_file_exists "$F"
assert_file_size   "$F" 4000 24000

assert_contains "$F" "Pivot to the kit"
assert_contains "$F" "northeast-denture-clinic"
assert_contains "$F" "market-mall-denture"
assert_contains "$F" "Northeast Denture Clinic"
assert_contains "$F" "Market Mall Denture Clinic"
assert_contains "$F" "Gia Huy"
assert_contains "$F" "giahuy.l.hoang@gmail.com"
assert_contains "$F" "AI Greeting"
assert_contains "$F" "AI Routing"
assert_contains "$F" "AI Services"
assert_contains "$F" "AI Knowledge"
assert_contains "$F" "data/ai_config.js"
assert_contains "$F" "Sign in to your workspace"
assert_contains "$F" "rrd-clinic-switcher"
assert_contains "$F" "rrd-profile-pill"
assert_contains "$F" "Phase 0 v3"

# Begins with markdown heading
assert_grep_count "$F" "^# " 1 8

test_summary
