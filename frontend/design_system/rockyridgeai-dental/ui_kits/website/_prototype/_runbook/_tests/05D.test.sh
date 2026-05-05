#!/usr/bin/env bash
# Test for Task 05D — data/ai_config.js (new)
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="data/ai_config.js"

assert_file_exists "$F"
assert_file_size   "$F" 4000 20000

assert_contains "$F" "window.AI_CONFIG"
assert_contains "$F" "northeast-denture-clinic"
assert_contains "$F" "market-mall-denture"
assert_contains "$F" "routing"
assert_contains "$F" "greeting"
assert_contains "$F" "ai_bookable_service_ids"
assert_contains "$F" "knowledge_docs"
assert_contains "$F" "denture_faq.md"
assert_contains "$F" "practice_info.md"
assert_contains "$F" "+15879738089"
assert_contains "$F" "+13682990959"
assert_contains "$F" "sip:34.130.210.160:5060"
assert_contains "$F" "Market Mall Denture Clinic, how can I help?"
assert_contains "$F" "clinic_approved"
assert_contains "$F" "pending_review"
assert_contains "$F" "SVC-001"

# knowledge_docs appears twice (one per clinic)
assert_grep_count "$F" "knowledge_docs:" 2 2

# IIFE wrapper
assert_grep_count "$F" "^\\(function" 1 1

test_summary
