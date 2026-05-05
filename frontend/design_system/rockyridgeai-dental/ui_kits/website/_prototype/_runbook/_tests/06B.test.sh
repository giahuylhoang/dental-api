#!/usr/bin/env bash
# Test for Task 06B — Branding sweep
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

# 9 files: 8 admin-*.html + AdminSidebar.jsx
PROT="ui_kits/website/_prototype"
PAGES=(
  "$PROT/admin-shell.html"
  "$PROT/admin-dashboard.html"
  "$PROT/admin-calls.html"
  "$PROT/admin-call-detail.html"
  "$PROT/admin-patients.html"
  "$PROT/admin-schedule.html"
  "$PROT/admin-routing.html"
  "$PROT/admin-greeting.html"
)

# Each admin-*.html title must contain "Rockyridge Dental AI"
for p in "${PAGES[@]}"; do
  assert_file_exists "$p"
  assert_contains   "$p" "Rockyridge Dental AI"
done

# AdminSidebar.jsx wordmark must be DENTAL AI
SB="$PROT/AdminSidebar.jsx"
assert_file_exists "$SB"
assert_contains   "$SB" "DENTAL AI"

# Only the OLD brand variants are banned. The new "AI Receptionist" signature
# (added as a mode badge + sidebar overline in v3 polish) is intentional.
for p in "${PAGES[@]}" "$SB"; do
  assert_absent "$p" "Rockyridge Receptionist"
  assert_absent "$p" "The Receptionist"
  assert_absent "$p" "RECEPTIONIST"
done

test_summary
