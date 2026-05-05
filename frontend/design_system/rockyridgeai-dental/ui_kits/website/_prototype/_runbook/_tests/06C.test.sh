#!/usr/bin/env bash
# Test for Task 06C — admin_mock.js refactor + ai_config.js disclosure/voice seeds
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

M="data/admin_mock.js"
A="data/ai_config.js"

# admin_mock.js shape
assert_file_exists "$M"
assert_file_size   "$M" 22000 90000
assert_contains   "$M" "window.ADMIN_MOCK"
assert_contains   "$M" "CLINICS"
assert_contains   "$M" "northeast-denture-clinic"
assert_contains   "$M" "market-mall-denture"
assert_contains   "$M" "Northeast Denture Clinic"
assert_contains   "$M" "Market Mall Denture Clinic"
assert_contains   "$M" "setCurrentClinic"
assert_contains   "$M" "clinic-changed"
assert_contains   "$M" "getClinic"
assert_grep_count "$M" "buildClinic\\(" 1 4

# ai_config.js disclosure + voice for both clinics
assert_file_exists "$A"
assert_file_size   "$A" 5000 28000
assert_grep_count "$A" "disclosure:" 2 2
assert_grep_count "$A" "voice:" 2 2
assert_contains   "$A" "ai_disclosure_required"
assert_contains   "$A" "ai_disclosure_phrase"
assert_contains   "$A" "assistant_name"
assert_contains   "$A" "provider_title"
assert_contains   "$A" "reason_question"
assert_contains   "$A" "Denturist"
assert_contains   "$A" "Dental AI"

test_summary
