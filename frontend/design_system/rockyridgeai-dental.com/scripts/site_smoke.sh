#!/usr/bin/env bash
# site_smoke.sh — site-wide smoke test for Rockyridge Dental AI design system
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$ROOT/ui_kits/website"
PORT=51789
fail=0

green() { echo "  ✓ $*"; }
red()   { echo "  ✗ $*"; fail=1; }

# ── 1. Start HTTP server ──────────────────────────────────────────────────────
python3 -m http.server "$PORT" --directory "$ROOT" >/dev/null 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null; exit $fail' EXIT INT TERM
sleep 1  # let server start

# ── 2. HTTP 200 for every .html in ui_kits/website/ ──────────────────────────
echo "[check 2] HTTP 200 for all HTML pages"
for f in "$WEB"/*.html; do
  name="$(basename "$f")"
  status=$(curl -sI "http://127.0.0.1:$PORT/ui_kits/website/$name" | head -1 | grep -oE '[0-9]{3}' | head -1)
  if [[ "$status" == "200" ]]; then
    green "$name → 200"
  else
    red "$name → $status (expected 200)"
  fi
done

# ── 3. Every <a href="…html…"> target exists ─────────────────────────────────
echo "[check 3] HTML href targets exist"
while IFS= read -r href; do
  # strip query/fragment
  target="${href%%\?*}"
  target="${target%%#*}"
  [[ "$target" == *.html ]] || continue
  # only relative (no scheme)
  [[ "$target" == http* ]] && continue
  if [[ -f "$WEB/$target" ]]; then
    green "href $target exists"
  else
    red "href $target not found in $WEB"
  fi
done < <(grep -hEo '<a href="[^"]*\.html[^"]*"' "$WEB"/*.html "$WEB"/*.jsx 2>/dev/null \
         | grep -oE '"[^"]*"' | tr -d '"' | sort -u)

# ── 4. Every local <script src="…"> exists ───────────────────────────────────
echo "[check 4] script src files exist"
for page in "$WEB"/*.html; do
  page_dir="$(dirname "$page")"
  while IFS= read -r src; do
    [[ "$src" == http* ]] && continue
    resolved="$page_dir/$src"
    # normalise path
    resolved="$(cd "$(dirname "$resolved")" 2>/dev/null && pwd)/$(basename "$resolved")" 2>/dev/null || true
    if [[ -f "$resolved" ]]; then
      green "$(basename "$page"): $src"
    else
      red "$(basename "$page"): $src not found (resolved: $resolved)"
    fi
  done < <(grep -Eo '<script src="[^"]*"' "$page" | grep -v 'https://' | grep -oE '"[^"]*"' | tr -d '"')
done

# ── 5. Every window.UPPER_SNAKE is referenced by an HTML page or data/index.js ─
echo "[check 5] window globals referenced"
while IFS= read -r global; do
  name="${global#window.}"
  lower="$(echo "$name" | tr '[:upper:]' '[:lower:]')"
  # check HTML pages (exact name) or data/index.js (lowercase/snake_case form)
  if grep -qr "$name" "$WEB"/*.html 2>/dev/null || \
     grep -qi "$lower" "$ROOT/data/index.js" 2>/dev/null; then
    green "$global referenced"
  else
    red "$global not referenced in any HTML page or data/index.js"
  fi
done < <(grep -hEo 'window\.[A-Z_]+' "$ROOT/data"/*.js | sort -u)

# ── 6. dashboard.html contains at least one numeric KPI ──────────────────────
echo "[check 6] dashboard.html has numeric KPI"
if grep -qE '[0-9]{3,}' "$WEB/dashboard.html"; then
  green "dashboard.html contains numeric KPI"
else
  red "dashboard.html has no numeric KPI string"
fi

# ── Final result ──────────────────────────────────────────────────────────────
if [[ $fail -ne 0 ]]; then
  echo "SMOKE FAILED"
  exit 1
fi
echo "SMOKE PASSED"
