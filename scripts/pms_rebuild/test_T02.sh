#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/giahuyhoangle/Projects/dental-api"
cd "$ROOT"
test -f web/styles/design-tokens.css || { echo "FAIL: design-tokens.css missing"; exit 1; }
diff -q web/styles/design-tokens.css /Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/colors_and_type.css >/dev/null \
  || { echo "FAIL: design-tokens.css does not match source"; exit 1; }
test -f web/tailwind.config.ts || { echo "FAIL: tailwind.config.ts missing"; exit 1; }
grep -q 'sidebar' web/tailwind.config.ts || { echo "FAIL: sidebar tokens not bound"; exit 1; }
grep -q 'design-tokens.css' web/app/layout.tsx || { echo "FAIL: design-tokens.css not imported in app/layout.tsx"; exit 1; }
# token guard
hex_hits=$(grep -RInE '#[0-9A-Fa-f]{3,8}\b' web/app web/components web/lib 2>/dev/null | grep -v node_modules | grep -v 'design-tokens.css' || true)
if [[ -n "$hex_hits" ]]; then echo "FAIL: raw hex outside tokens file:"; echo "$hex_hits"; exit 1; fi
( cd web && npx next build ) || { echo "FAIL: next build"; exit 1; }
echo "PASS T02"
