# Extract `frontend/` from dental-api — Design

**Date:** 2026-05-19
**Status:** Approved (design phase)
**Owner:** Gia Huy
**Branch:** `pms-frontend-overhaul` (layered on top of the v1 router refactor)

## Goal

Move `dental-api/frontend/` (a Next.js 16 / React 19 CRM/PMS app) out of the `dental-api` repository into a new sibling repository at `dental-system/dental-crm-frontend/`. Preserve commit history of frontend-only changes. Remove the corresponding files and configuration from `dental-api`.

## Why

The two codebases share nothing but an HTTP contract. They have different toolchains (uv/pytest vs npm/Next.js), different deploy targets (Cloud Run vs Firebase App Hosting), different CI needs, and different release cadences. Keeping them in one repo bloats `ls`, slows greps, complicates CLAUDE.md, and is the single biggest source of noise when working on the API.

## Non-Goals

- Creating a GitHub repository for the new frontend (`gh repo create dental-crm-frontend`) — manual follow-up.
- Re-pointing Firebase App Hosting at the new GitHub repository — manual step in the Firebase Console.
- Rewriting or pruning frontend-related history out of `dental-api` itself (this would require `git filter-repo --invert-paths` on the dental-api repo, which is destructive for anyone else who has cloned it). The frontend commits stay in dental-api's history as historical artifacts.
- Touching the v1 router refactor work already on `pms-frontend-overhaul`. The frontend extraction is layered on top as additional commits.
- Changing the CORS allow-list in `api/main.py` — the frontend continues to deploy to the same Firebase App Hosting URL (`dental-crm--rockyridgeai-dental.us-central1.hosted.app`), so the existing entry remains valid.

## Constraints

1. **History preservation.** Frontend commits (e.g. `9008072 feat(crm): new-booking SSE popup`, `2751a42 add new busy block`) must survive the move with their original commit messages and authorship. SHAs will change — that's inherent to `git filter-repo`.
2. **No cross-boundary imports.** `frontend/src/` must not import from anywhere outside `frontend/` (verified — no matches for `../..` or `../api` patterns in `frontend/src/`).
3. **dental-api stays buildable + tested.** The existing test gate (`tests/test_contract_v1.py` etc.) must remain green after the extraction.
4. **Firebase App Hosting URL stays the same.** No CORS regression.

## Inputs / Prerequisites

- `git-filter-repo` (third-party tool, separate from git). Not currently installed — install via `brew install git-filter-repo` as Step 0.
- Clean working tree on `pms-frontend-overhaul` after Task 13 of the v1 refactor.
- macOS host (paths use `/Users/giahuyhoangle/Projects/dental-system/...`).

## Target Layout

```
dental-system/
├── dental-api/                         (unchanged besides the deletions below)
│   ├── api/                            (router refactor work — preserved)
│   ├── services/
│   ├── tools/
│   ├── tests/
│   ├── database/
│   ├── docs/
│   ├── CLAUDE.md                       (Design System sections removed)
│   ├── apphosting.yaml                 ← REMOVED (moves to new repo)
│   ├── frontend/                       ← REMOVED
│   ├── dental-calendar/                ← REMOVED (was empty)
│   └── ...
│
├── dental-crm-frontend/                ← NEW REPO (local-only initially)
│   ├── .git/                           (filtered history; SHAs renumbered)
│   ├── apphosting.yaml                 (moved from dental-api/)
│   ├── src/
│   ├── design_system/
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   ├── eslint.config.mjs
│   ├── postcss.config.mjs
│   ├── CLAUDE.md                       (copied from frontend/CLAUDE.md)
│   ├── README.md                       (updated to reflect new home)
│   └── ...
│
├── dental-agent/
├── references/
└── ...
```

## Sequence

Each step is a self-contained operation. The dental-api commits land on the `pms-frontend-overhaul` branch (per user decision — layered on the router refactor, not split into a separate branch).

### Step 0: Install `git-filter-repo`

```bash
brew install git-filter-repo
which git-filter-repo  # confirm
```

### Step 1: Verify pre-conditions in dental-api

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
git rev-parse --abbrev-ref HEAD   # expect: pms-frontend-overhaul
git status --porcelain | grep -v '^??'   # expect: empty (no tracked modifications)
.venv/bin/python -m pytest tests/test_contract_v1.py tests/test_api.py -q   # baseline green
```

If anything is dirty (tracked modifications) or tests fail, STOP — that's an unrelated state to clean up first.

### Step 2: Confirm no cross-boundary imports

```bash
grep -rln '\.\./\.\.\|\.\./api\b\|@dental-api' frontend/src
```

Expect: empty. (Verified during design.) If any matches appear, the frontend has a hidden dependency on dental-api code — STOP and surface for user decision.

### Step 3: Clone dental-api to a temp location and filter it

```bash
TEMP=$(mktemp -d)
git clone /Users/giahuyhoangle/Projects/dental-system/dental-api "$TEMP/extracted"
cd "$TEMP/extracted"
git filter-repo --subdirectory-filter frontend
```

`filter-repo` rewrites history so:
- Only commits that touched `frontend/` survive
- `frontend/` becomes the new repository root (no more `frontend/` prefix)
- SHAs are renumbered (expected)
- `origin` remote is removed by default (this is fine — new repo)

Verify the result:

```bash
ls -la "$TEMP/extracted"
# expect: src/, design_system/, package.json, next.config.ts, CLAUDE.md, etc.
test -f "$TEMP/extracted/package.json" && echo "package.json OK"
test -d "$TEMP/extracted/src" && echo "src/ OK"
test -d "$TEMP/extracted/design_system" && echo "design_system/ OK"
git -C "$TEMP/extracted" log --oneline | head -10
# expect: real frontend commits (new SHAs but recognizable messages)
git -C "$TEMP/extracted" log --oneline | wc -l
# expect: > 0; should be in the dozens at minimum
```

If any of these checks fail, STOP and report — do NOT proceed to step 4 (which is destructive).

### Step 4: Move the filtered clone into place

```bash
mv "$TEMP/extracted" /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend
```

Verify:

```bash
ls /Users/giahuyhoangle/Projects/dental-system/
# expect: dental-api, dental-agent, dental-crm-frontend (new), references, ...
git -C /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend status
# expect: clean working tree; HEAD points at the latest filtered commit
```

### Step 5: Move `apphosting.yaml` into the new repo

`apphosting.yaml` lives at `dental-api/apphosting.yaml` today (NOT inside `frontend/`, so `filter-repo` didn't carry it over). It's the Firebase App Hosting config for the frontend — it belongs in the new repo.

```bash
cp /Users/giahuyhoangle/Projects/dental-system/dental-api/apphosting.yaml \
   /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend/apphosting.yaml
cd /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend
git add apphosting.yaml
git commit -m "chore: bring apphosting.yaml from dental-api at extraction time"
```

> The file (verified at design time) contains only `runConfig` (CPU/memory/concurrency) and an `env` block declaring `NEXT_PUBLIC_API_BASE`. No path references, so no edits needed during the copy.

### Step 6: Smoke-test the new repo

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend
rm -rf node_modules .next  # stale from the live working tree (won't exist in filtered clone)
npm install
npm run build
```

Expect: install completes, build succeeds. Report build output to the user.

If build fails, do NOT proceed to step 7. The failure means the extraction isn't viable as-is and we need to debug what's missing (e.g. a config file outside `frontend/` that the build relied on).

### Step 7: Update README and CLAUDE.md in the new repo

The new repo inherits `README.md` and `CLAUDE.md` from `frontend/`. Both likely reference `dental-api` paths or "this is part of dental-api". Update them:

- `README.md`: Brief mention of "this is the CRM/PMS frontend for dental-api; backend lives at `dental-system/dental-api/` (or `<github-org>/dental-api` once published)". Add a "Setup" section with `npm install && npm run dev`. Don't expand beyond what's needed.
- `CLAUDE.md`: Strip references to dental-api paths. Keep the Design System guidance (that's frontend-specific). Note the API base URL is configurable via env (see existing `next.config.ts` or `.env.local` patterns).

Commit:

```bash
git add README.md CLAUDE.md
git commit -m "docs: update README and CLAUDE.md for standalone repo"
```

### Step 8: Remove the frontend from dental-api

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
git rm -r frontend/
rmdir dental-calendar/   # was empty
git rm apphosting.yaml
```

Note: `rmdir` only succeeds on an empty directory. If `dental-calendar/` has any files (it shouldn't, per design exploration), STOP and surface.

### Step 9: Update `dental-api/CLAUDE.md`

Remove the entire "Design System (mandatory for all frontend/UI work)" section (lines 71-94 in the current CLAUDE.md) and the "Things to know" bullets that reference frontend (lines 96-99 — "Ignore existing styling in `frontend/src/`", "Ignore `frontend/design_system/...`", etc.).

Replace with a single line under "Things to know":

```markdown
- The CRM/PMS frontend used to live at `frontend/`; it now lives in the sibling repo `dental-system/dental-crm-frontend/`.
```

Also remove the `apphosting.yaml` mention in the deploy section of `CLAUDE.md` if there is one.

### Step 10: Commit the dental-api side

```bash
git add CLAUDE.md
git commit -m "refactor: extract frontend into dental-crm-frontend sibling repo

Removes frontend/, apphosting.yaml, and the empty dental-calendar/
directory. The frontend now lives at dental-system/dental-crm-frontend/
with its own .git (history preserved via git filter-repo).

CLAUDE.md no longer carries the Design System section; that documentation
now lives with the frontend code. Existing CORS allow-list entries for
Firebase App Hosting remain — the frontend continues to deploy at the
same URL."
```

### Step 11: Run dental-api tests one last time

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
.venv/bin/python -m pytest -q
```

Expect: 286 passed (or whatever the current baseline is post-v1-refactor). The API code didn't change, so this should be unaffected.

## What's still manual after this lands

Documented in the new repo's README:

1. **Create GitHub repo:** `cd dental-crm-frontend && gh repo create dental-crm-frontend --private --source . --remote origin --push`
2. **Re-link Firebase App Hosting** in the Firebase Console to the new GitHub repository.
3. **Update any CI references** that point at `dental-api/frontend/` (none known today, but worth a search after the move).
4. **Update local IDE workspaces** if you have a `.code-workspace` file rooted at `dental-api/`.

## Risk + mitigation

| Risk | Mitigation |
|---|---|
| `git-filter-repo` not installed | Step 0 installs it |
| Filtered repo missing files because they were committed outside `frontend/` | Step 3 verification; specifically called out: `apphosting.yaml` is at `dental-api/` root, NOT under `frontend/` — handled separately in step 5 |
| Hidden cross-boundary imports in `frontend/src/` | Step 2 verifies; pre-design check found none |
| `npm run build` fails in the new repo (something the old in-monorepo setup provided implicitly) | Step 6 smoke test catches this BEFORE step 8 deletes anything; we can investigate without losing state |
| `dental-calendar/` not empty when we try `rmdir` | `rmdir` fails loudly; we surface, decide what's in there |
| `apphosting.yaml` has path references that break in the new repo | Verified at design time: no path references in the file (only runConfig + env). No adjustment needed. |
| `pms-frontend-overhaul` branch (the v1 refactor) merge to main now has both refactors bundled | This is what the user asked for — both refactors land together. Reviewer pre-warned via the commit message. |
| Firebase App Hosting deploy breaks until console is re-pointed | Documented as manual follow-up; the apphosting.yaml + code are correct, only the Console hookup is manual |

## Open Questions

None at design time. Any ambiguity discovered during a step (e.g. apphosting.yaml has paths needing adjustment, dental-calendar/ unexpectedly has files) is resolved by **stopping and surfacing to the user**, not by making an undocumented call.
