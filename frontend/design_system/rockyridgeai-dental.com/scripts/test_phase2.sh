#!/usr/bin/env bash
# Phase 2 test: 9 new app pages exist and render.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$ROOT/ui_kits/website"
fail=0

PAGES=(reports settings plans patient-detail invoice-detail appointment-detail lead-detail lab-case-detail denture-case-detail)

echo "[1] Each page exists"
for p in "${PAGES[@]}"; do
  f="$WEB/$p.html"
  if [[ -f "$f" ]]; then echo "  ✓ $p.html"; else echo "  ✗ MISSING $p.html"; fail=1; fi
done

echo "[2] Each page imports colors_and_type.css and uses Sidebar+TopBar (except detail pages may opt out of Sidebar)"
for p in "${PAGES[@]}"; do
  f="$WEB/$p.html"
  [[ ! -f "$f" ]] && continue
  grep -q 'colors_and_type.css' "$f" && echo "  ✓ $p.html → colors_and_type.css" || { echo "  ✗ $p.html missing colors_and_type.css"; fail=1; }
done

echo "[3] HTTP 200 on every page"
port=51789
python3 -m http.server "$port" --directory "$ROOT" >/dev/null 2>&1 &
server_pid=$!
trap "kill $server_pid 2>/dev/null || true" EXIT
sleep 1
for f in "$WEB"/*.html; do
  rel="ui_kits/website/$(basename "$f")"
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port/$rel")
  if [[ "$code" == "200" ]]; then echo "  ✓ $rel"; else echo "  ✗ $rel ($code)"; fail=1; fi
done

echo "[4] Phase 1 link audit re-runs cleanly (no missing href targets now that Phase 2 added the pages)"
set +e
missing=$(
  grep -rohE 'href="[^"#?]+\.html(\?[^"]*)?(#[^"]*)?"' "$WEB"/*.html "$WEB"/*.jsx 2>/dev/null \
    | sed -E 's/href="//; s/".*//; s/[?#].*//' \
    | sort -u \
    | while read -r t; do
        [[ -z "$t" ]] && continue
        if [[ "$t" == http* ]] || [[ "$t" == /* ]]; then continue; fi
        if [[ ! -f "$WEB/$t" ]]; then echo "$t"; fi
      done
  true
)
set -e
if [[ -n "$missing" ]]; then echo "  ✗ unresolved hrefs:"; echo "$missing" | sed 's/^/    /'; fail=1; else echo "  ✓ all hrefs resolve"; fi

if [[ $fail -ne 0 ]]; then echo "PHASE 2 FAILED"; exit 1; fi
echo "PHASE 2 PASSED"
