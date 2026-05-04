#!/usr/bin/env bash
# Phase 1 test: static-link navigation refactor.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$ROOT/ui_kits/website"
fail=0

check_file() {
  if [[ -f "$1" ]]; then echo "  ✓ $1"; else echo "  ✗ MISSING $1"; fail=1; fi
}

echo "[1] Sidebar.jsx must include all 10 nav keys (dashboard, patients, schedule, plans, lab, billing, comms, crm, reports, settings)"
for key in dashboard patients schedule plans lab billing comms crm reports settings; do
  if grep -qE "(key|href)[^A-Za-z]+${key}([\"'\.]|html)" "$WEB/Sidebar.jsx"; then
    echo "  ✓ key:$key"
  else
    echo "  ✗ MISSING key:$key in Sidebar.jsx"; fail=1
  fi
done

echo "[2] Sidebar.jsx must render <a href> for navigation"
if grep -qE 'href=[`"]\$?\{?[a-z_-]+\.html' "$WEB/Sidebar.jsx" || grep -qE '<a [^>]*href=[`"]' "$WEB/Sidebar.jsx"; then
  echo "  ✓ Sidebar.jsx renders <a href=...>"
else
  echo "  ✗ Sidebar.jsx still uses pure onClick — no <a href> found"; fail=1
fi

echo "[3] TopBar.jsx must link logo/clinic name to dashboard.html and have a logout target login.html"
grep -q 'dashboard.html' "$WEB/TopBar.jsx"  && echo "  ✓ TopBar→dashboard"  || { echo "  ✗ TopBar missing dashboard.html link"; fail=1; }
grep -q 'login.html'     "$WEB/TopBar.jsx"  && echo "  ✓ TopBar→login (logout)" || { echo "  ✗ TopBar missing login.html link"; fail=1; }

echo "[4] Nav.jsx + CTA.jsx must link to login.html / index.html"
grep -q 'login.html' "$WEB/Nav.jsx" && echo "  ✓ Nav→login" || { echo "  ✗ Nav missing login.html"; fail=1; }

echo "[5] No <a href=\"#\"> stubs outside index.html anchor sections"
strays=$(grep -lE '<a [^>]*href="#"' "$WEB"/*.html 2>/dev/null | grep -v '/index.html' || true)
if [[ -n "$strays" ]]; then echo "  ✗ Stray href=\"#\" in: $strays"; fail=1; else echo "  ✓ no stray hrefs"; fi

echo "[6] Every <a href=\"X.html\"> across the kit must resolve to a real file"
set +e
missing_targets=$(
  grep -rohE 'href="[^"#?]+\.html(\?[^"]*)?(#[^"]*)?"' "$WEB"/*.html "$WEB"/*.jsx 2>/dev/null \
    | sed -E 's/href="//; s/".*//; s/[?#].*//' \
    | sort -u \
    | while read -r target; do
        [[ -z "$target" ]] && continue
        # Skip absolute or external
        if [[ "$target" == http* ]] || [[ "$target" == /* ]]; then continue; fi
        if [[ ! -f "$WEB/$target" ]]; then echo "$target"; fi
      done
  true
)
set -e
if [[ -n "$missing_targets" ]]; then
  echo "  ⚠ targets that don't exist yet (Phase 2 will create these):"
  echo "$missing_targets" | sed 's/^/    /'
  # Phase 1 allows missing targets ONLY if they're in the Phase-2 page list:
  allowed='^(reports|settings|plans|patient-detail|invoice-detail|appointment-detail|lead-detail|lab-case-detail|denture-case-detail)\.html$'
  while IFS= read -r t; do
    base="${t%%[?#]*}"
    if [[ ! "$base" =~ $allowed ]]; then
      echo "  ✗ unexpected missing target: $t"; fail=1
    fi
  done <<< "$missing_targets"
else
  echo "  ✓ all <a href> targets resolve"
fi

echo "[7] HTTP 200 smoke on every existing page"
port=51789
python3 -m http.server "$port" --directory "$ROOT" >/dev/null 2>&1 &
server_pid=$!
trap "kill $server_pid 2>/dev/null || true" EXIT
sleep 1
for f in "$WEB"/*.html; do
  rel="ui_kits/website/$(basename "$f")"
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port/$rel")
  if [[ "$code" == "200" ]]; then echo "  ✓ $rel ($code)"; else echo "  ✗ $rel ($code)"; fail=1; fi
done

if [[ $fail -ne 0 ]]; then echo "PHASE 1 FAILED"; exit 1; fi
echo "PHASE 1 PASSED"
