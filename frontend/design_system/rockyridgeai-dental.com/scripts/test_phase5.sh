#!/usr/bin/env bash
# Phase 5 test: simulated auth flow.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$ROOT/ui_kits/website"
LIB="$ROOT/lib"
fail=0

echo "[1] lib/auth.js exists and exports the expected API"
if [[ ! -f "$LIB/auth.js" ]]; then echo "  ✗ MISSING lib/auth.js"; fail=1; fi
for fn in login logout getSession requireSession; do
  grep -q "RRD\.$fn\b\|window\.$fn\b\|\b$fn\s*[:=]\s*function" "$LIB/auth.js" 2>/dev/null && echo "  ✓ $fn defined" || { echo "  ✗ auth.$fn missing"; fail=1; }
done

echo "[2] login.html wires the form to RRD.login() and redirects to dashboard.html"
grep -q 'RRD\.login\|window\.RRD\.login\|auth\.login' "$WEB/login.html" && echo "  ✓ login.html calls login()" || { echo "  ✗ login.html does not call login()"; fail=1; }
grep -q 'dashboard.html' "$WEB/login.html" && echo "  ✓ login.html → dashboard.html" || { echo "  ✗ login.html missing dashboard redirect"; fail=1; }

echo "[3] Every app page (except login.html and index.html) gates with requireSession()"
for f in "$WEB"/*.html; do
  base="$(basename "$f")"
  case "$base" in login.html|index.html) continue;; esac
  if grep -q 'RRD\.requireSession\|requireSession()' "$f"; then
    echo "  ✓ $base gated"
  else
    echo "  ✗ $base does not call requireSession"; fail=1
  fi
done

echo "[4] TopBar has a logout link"
grep -q 'logout\|RRD\.logout' "$WEB/TopBar.jsx" && echo "  ✓ TopBar wires logout" || { echo "  ✗ TopBar missing logout"; fail=1; }

if [[ $fail -ne 0 ]]; then echo "PHASE 5 FAILED"; exit 1; fi
echo "PHASE 5 PASSED"
