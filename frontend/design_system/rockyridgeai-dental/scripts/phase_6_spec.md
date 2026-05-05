# Phase 6 — Site-wide smoke + INDEX.md hand-off

## Goal

Ship the bundle: write `scripts/site_smoke.sh` that runs ALL final checks at once, plus an `INDEX.md` site map under `ui_kits/website/`.

## Working directory

`frontend/design_system/rockyridgeai-dental.com/`

## Files to create

### 1. `scripts/site_smoke.sh`

A bash script that:
1. Starts `python3 -m http.server <port>` rooted at the design-system folder (`$(dirname $0)/..`). Use a free port (e.g. 51789) and trap-kill on exit.
2. `curl -sI` every `.html` in `ui_kits/website/` and assert HTTP 200.
3. Greps every `<a href="…html…">` in HTML+JSX files and asserts each target file exists in `ui_kits/website/`.
4. Greps every `<script src="…">` reference and asserts the script file exists (paths are relative; resolve them against the page's directory).
5. Greps every `window.<UPPER_SNAKE>` definition in `data/*.js` and asserts each global is referenced by at least one HTML page or by `data/index.js`.
6. Greps `dashboard.html` for at least one numeric KPI string (e.g. `1284` or `42`) — proves seed data is consumed.
7. Echo green-tick lines for each passing check; red-cross + non-zero exit for any failure.

The script must be self-contained (no extra deps beyond `python3`, `curl`, `grep`, `bash`).

### 2. `ui_kits/website/INDEX.md`

A site map. For each HTML page, one row with: file name · purpose · Sidebar key · which `data/*.js` files it loads · which JSX components it uses.

Include a short "How to run" section at the top:
```
cd frontend/design_system/rockyridgeai-dental.com
python3 -m http.server 5180
open http://127.0.0.1:5180/ui_kits/website/index.html
```

Include a "Auth" note: any password ≥ 6 chars logs you in as the first demo user.

### 3. (Optional) `scripts/run_all.sh` — already exists from scaffolding. Verify it short-circuits on failure.

## Pass criterion

Run `bash scripts/test_phase6.sh`. It checks:
1. `scripts/site_smoke.sh` exists and is executable.
2. `ui_kits/website/INDEX.md` exists and references every HTML page.
3. `bash scripts/site_smoke.sh` exits 0.

## Rules

- Don't add backend dependencies, npm packages, or Python packages — pure stdlib.
- Don't change any HTML/JSX in this phase except small fixups if `site_smoke.sh` reveals broken links.
- INDEX.md uses the same brand voice as `README.md`: authoritative, calm, definite article on system parts.
