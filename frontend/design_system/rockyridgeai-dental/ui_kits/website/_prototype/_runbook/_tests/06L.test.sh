#!/usr/bin/env bash
# Test for Task 06L — End-to-end Plan v3 integrity
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

# 0. Stub markdown exists
assert_file_exists "ui_kits/website/_prototype/_runbook/06L-verify.md"

PROT="ui_kits/website/_prototype"
PAGES_EXISTING=(
  "$PROT/admin-shell.html"
  "$PROT/admin-dashboard.html"
  "$PROT/admin-calls.html"
  "$PROT/admin-call-detail.html"
  "$PROT/admin-patients.html"
  "$PROT/admin-schedule.html"
  "$PROT/admin-routing.html"
  "$PROT/admin-greeting.html"
)

# 1. Branding sweep — every existing admin-*.html title contains Dental AI;
#    OLD brand variants ("Rockyridge Receptionist", "The Receptionist",
#    "RECEPTIONIST" wordmark) are absent. The signature "AI Receptionist"
#    is intentional and allowed.
for p in "${PAGES_EXISTING[@]}"; do
  assert_contains "$p" "Rockyridge Dental AI"
  assert_absent  "$p" "Rockyridge Receptionist"
  assert_absent  "$p" "The Receptionist"
  assert_absent  "$p" "RECEPTIONIST"
done
assert_contains "$PROT/AdminSidebar.jsx" "DENTAL AI"
assert_absent  "$PROT/AdminSidebar.jsx" "RECEPTIONIST"
assert_absent  "$PROT/AdminSidebar.jsx" "Rockyridge Receptionist"

# 2. AdminSidebar clinic switcher
assert_contains "$PROT/AdminSidebar.jsx" "rrd-clinic-switcher"
assert_contains "$PROT/AdminSidebar.jsx" "data-clinic-id"

# 3. Profile pill on every existing admin-*.html
for p in "${PAGES_EXISTING[@]}"; do
  assert_grep_count "$p" 'id="rrd-profile-pill"' 1 1
done

# 4. admin_mock keyed by clinic_id
M="data/admin_mock.js"
assert_contains "$M" "setCurrentClinic"
assert_contains "$M" "northeast-denture-clinic"
assert_contains "$M" "market-mall-denture"

# 5. Four new pages exist with verbatim
NEW_PAGES=(
  "$PROT/admin-services.html"
  "$PROT/admin-knowledge.html"
  "$PROT/admin-disclosure.html"
  "$PROT/admin-voice.html"
)
for p in "${NEW_PAGES[@]}"; do
  assert_file_exists "$p"
  assert_contains   "$p" "Rockyridge Dental AI"
  assert_grep_count "$p" 'id="rrd-profile-pill"' 1 1
done
assert_contains "$PROT/admin-services.html"   "Save service catalogue"
assert_contains "$PROT/admin-knowledge.html"  "Save knowledge updates"
assert_contains "$PROT/admin-disclosure.html" "Save disclosure"
assert_contains "$PROT/admin-voice.html"      "Save voice"

# 6. AdminSidebar config group has 6 children
SB="$PROT/AdminSidebar.jsx"
for key in routing greeting services knowledge disclosure voice; do
  assert_contains "$SB" "key: '$key'"
done

# 7. Kit Sidebar.jsx cross-link
KS="ui_kits/website/Sidebar.jsx"
assert_contains "$KS" "ai-receptionist"
assert_contains "$KS" "AI Receptionist"
assert_contains "$KS" "_prototype/admin-dashboard.html"
assert_contains "$KS" "relogin=1"
assert_contains "$KS" "isNew"
assert_contains "$KS" "NEW"

# 8. Kit Sidebar.jsx still has all 10 original nav keys
for key in dashboard patients schedule plans lab billing comms crm reports settings; do
  assert_contains "$KS" "key: '$key'"
done

# 9. ai_config.js disclosure + voice for both clinics
A="data/ai_config.js"
assert_grep_count "$A" "disclosure:" 2 2
assert_grep_count "$A" "voice:" 2 2

# 10. AI Receptionist signature — every prototype page passes mode prop;
#     AdminSidebar carries the mode overline. Kit pages MUST NOT carry it.
ALL_PROTO=( "${PAGES_EXISTING[@]}" "${NEW_PAGES[@]}" )
for p in "${ALL_PROTO[@]}"; do
  assert_contains "$p" 'mode'
  # Either JSX `mode="AI Receptionist"` or createElement form `mode: 'AI Receptionist'`
  assert_grep_count "$p" "mode[=:][ ]*['\\\"]AI Receptionist['\\\"]" 1 5
done
# AdminSidebar overline literal
assert_contains "$PROT/AdminSidebar.jsx" "AI Receptionist"
# TopBar.jsx exposes the mode prop
assert_contains "ui_kits/website/TopBar.jsx" "mode"
# Kit pages do NOT pass mode (no signature on PMS surface)
assert_grep_count "ui_kits/website/dashboard.html" "mode=\"AI Receptionist\"" 0 0
assert_grep_count "ui_kits/website/settings.html"  "mode=\"AI Receptionist\"" 0 0

test_summary
