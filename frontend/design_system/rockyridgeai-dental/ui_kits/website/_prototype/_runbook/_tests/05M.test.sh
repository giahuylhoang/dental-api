#!/usr/bin/env bash
# Test for Task 05M — End-to-end integrity
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

# 0. Stub markdown exists.
assert_file_exists "ui_kits/website/_prototype/_runbook/05M-verify.md"

# 1. data/clinics.js — both ids, with display_name
C="data/clinics.js"
assert_file_exists "$C"
assert_contains "$C" "id: \"northeast-denture-clinic\""
assert_contains "$C" "id: \"market-mall-denture\""
assert_contains "$C" "Northeast Denture Clinic"
assert_contains "$C" "Market Mall Denture Clinic"

# 2. data/users.js — owner first, both clinics in assigned_clinic_ids
U="data/users.js"
assert_file_exists "$U"
assert_contains "$U" "Gia Huy"
assert_contains "$U" "giahuy.l.hoang@gmail.com"
assert_contains "$U" "Owner"
assert_grep_count "$U" "assigned_clinic_ids:" 3 3

# 3. data/ai_config.js — routing+greeting+knowledge_docs per clinic
A="data/ai_config.js"
assert_file_exists "$A"
assert_grep_count "$A" "knowledge_docs:" 2 2
assert_grep_count "$A" "routing:" 2 2
assert_grep_count "$A" "greeting:" 2 2

# 4. lib/auth.js — new helpers + dispatch
L="lib/auth.js"
assert_file_exists "$L"
assert_contains "$L" "setCurrentClinic"
assert_contains "$L" "getCurrentClinicId"
assert_contains "$L" "getAssignedClinicIds"
assert_contains "$L" "clinic-changed"

# 5. Sidebar.jsx — switcher hooks
S="ui_kits/website/Sidebar.jsx"
assert_file_exists "$S"
assert_contains "$S" "rrd-clinic-switcher"
assert_contains "$S" "data-clinic-id"
assert_contains "$S" "Object.assign(window, { Sidebar })"

# 6. TopBar.jsx — profile menu hooks + sign out
T="ui_kits/website/TopBar.jsx"
assert_file_exists "$T"
assert_contains "$T" "rrd-profile-pill"
assert_contains "$T" "rrd-profile-menu"
assert_contains "$T" "Sign out"
assert_contains "$T" "Object.assign(window, { TopBar })"

# 7. settings.html — all 12 tabs in TABS
G="ui_kits/website/settings.html"
assert_file_exists "$G"
for t in 'Clinic info' 'Working hours' 'Operatories' 'Providers' 'Users & roles' 'Integrations' 'Notifications' 'Audit log' 'AI Greeting' 'AI Routing' 'AI Services' 'AI Knowledge'; do
  assert_contains "$G" "'$t'"
done

# 8. settings.html — verbatim binding strings
assert_contains "$G" "Welcome to … How can I help you today?"
assert_contains "$G" "0 / 280 characters"
assert_contains "$G" "AI SIP URI (read-only here; engineer-managed)"
assert_contains "$G" "Both blank means closed that day."
assert_contains "$G" "Save greeting"
assert_contains "$G" "Save routing"
assert_contains "$G" "Save service catalogue"
assert_contains "$G" "Save knowledge updates"

# 9. login.html — copy edit applied
LO="ui_kits/website/login.html"
assert_file_exists "$LO"
assert_contains "$LO" "Sign in to your workspace"
assert_absent  "$LO" "Sign in to your clinic"

test_summary
