#!/usr/bin/env bash
# Phase 6 test: site-wide smoke + INDEX.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$ROOT/ui_kits/website"
fail=0

echo "[1] scripts/site_smoke.sh exists and is executable"
[[ -x "$ROOT/scripts/site_smoke.sh" ]] && echo "  ✓ site_smoke.sh" || { echo "  ✗ site_smoke.sh missing or not executable"; fail=1; }

echo "[2] INDEX.md lists every HTML page"
if [[ ! -f "$WEB/INDEX.md" ]]; then echo "  ✗ INDEX.md missing"; fail=1; else
  for f in "$WEB"/*.html; do
    name="$(basename "$f")"
    grep -q "$name" "$WEB/INDEX.md" || { echo "  ✗ INDEX.md missing $name"; fail=1; }
  done
  echo "  ✓ INDEX.md covers all pages"
fi

echo "[3] site_smoke.sh runs cleanly"
if bash "$ROOT/scripts/site_smoke.sh"; then
  echo "  ✓ site_smoke.sh passes"
else
  echo "  ✗ site_smoke.sh failed"; fail=1
fi

if [[ $fail -ne 0 ]]; then echo "PHASE 6 FAILED"; exit 1; fi
echo "PHASE 6 PASSED"
