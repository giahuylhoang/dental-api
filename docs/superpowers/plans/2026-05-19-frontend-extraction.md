# Frontend Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `dental-api/frontend/` into a new sibling repo `dental-system/dental-crm-frontend/` with preserved git history, then remove the frontend from `dental-api`.

**Architecture:** Use `git filter-repo --subdirectory-filter frontend` on a temp clone of `dental-api` to produce a new repo where `frontend/` is the root and only frontend-touching commits remain. Move the filtered clone to its final path. Copy `apphosting.yaml` (lives at dental-api root, not under frontend/) into the new repo. Smoke-test build. Then remove `frontend/`, `apphosting.yaml`, and the empty `dental-calendar/` from dental-api, and strip Design System sections from `dental-api/CLAUDE.md`.

**Tech Stack:** git, git-filter-repo (third-party tool), npm, Next.js 16, pytest (for dental-api gate).

**Spec:** `docs/superpowers/specs/2026-05-19-frontend-extraction-design.md`

**Branch:** `pms-frontend-overhaul` (layered on top of the v1 router refactor, per user choice).

**Gate (dental-api side):** `.venv/bin/python -m pytest -q` must remain green (286 passed baseline). The API code isn't being touched, so this is just a sanity check at the end.

**Gate (new repo side):** `npm install && npm run build` must succeed in the new repo before any deletions happen in dental-api. Build failure = STOP and investigate; do NOT proceed to deletion.

**Key principle:** The destructive deletions in dental-api happen LAST (Tasks 8-10), after the new repo is fully smoke-tested. If anything goes wrong before Task 8, the working tree of dental-api is unchanged and we can debug without losing state.

---

## Task 0: Prereq — install `git-filter-repo`

**Files:** none (system-level install)

- [ ] **Step 1: Check if `git-filter-repo` is already installed**

```bash
which git-filter-repo
```

If output is a path (e.g. `/opt/homebrew/bin/git-filter-repo`), skip to Step 3. Otherwise continue.

- [ ] **Step 2: Install via Homebrew**

```bash
brew install git-filter-repo
```

Expected: install completes; `which git-filter-repo` now returns a path.

- [ ] **Step 3: Confirm version**

```bash
git-filter-repo --version
```

Expected: prints a version number (any version is fine; the `--subdirectory-filter` flag is stable across releases).

No commit. No code change.

---

## Task 1: Verify preconditions in dental-api

**Files:** none (read-only checks)

- [ ] **Step 1: Confirm branch and clean tree**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
git rev-parse --abbrev-ref HEAD
```

Expected: `pms-frontend-overhaul`. If different, STOP and surface to the user.

```bash
git status --porcelain | grep -v '^??'
```

Expected: empty output (no tracked modifications). Untracked files (lines starting with `??`) are fine; we won't touch them. If there are tracked modifications, STOP and surface.

- [ ] **Step 2: Confirm v1 refactor gate still green**

```bash
.venv/bin/python -m pytest tests/test_contract_v1.py tests/test_api.py -q 2>&1 | tail -3
```

Expected: e.g. `52 passed`. If anything fails, STOP — the frontend extraction shouldn't proceed against a broken baseline.

- [ ] **Step 3: Confirm no cross-boundary imports**

```bash
grep -rln '\.\./\.\.\|\.\./api\b\|@dental-api' frontend/src 2>/dev/null
```

Expected: empty output (verified at design time). If any match appears, STOP and surface to the user — the frontend has a hidden dependency on dental-api code that filter-repo will silently break.

- [ ] **Step 4: Confirm `apphosting.yaml` has no path edits needed**

```bash
cat apphosting.yaml
```

Expected: a YAML file with `runConfig:` (CPU/memory/concurrency) and an `env:` block declaring `NEXT_PUBLIC_API_BASE`. No `rootDirectory:` line, no `frontend/` path references. If you see a `rootDirectory:` line or any string containing `frontend/`, STOP and surface — the file will need editing before commit in Task 4.

No commit, no code change.

---

## Task 2: Clone + filter to a temp directory

**Files:**
- Create (temporarily): `/tmp/dental-extract-XXXXXX/extracted/` (a new local git repo)

- [ ] **Step 1: Make a temp directory and clone dental-api into it**

```bash
TEMP=$(mktemp -d)
echo "TEMP=$TEMP"
git clone /Users/giahuyhoangle/Projects/dental-system/dental-api "$TEMP/extracted"
```

Expected: a fresh clone at `$TEMP/extracted` containing the full dental-api repo. The clone has a remote called `origin` pointing at the local source path — that's fine; filter-repo will strip it.

> **Important:** Record the value of `$TEMP` somewhere persistent (e.g. write it to `/tmp/extract-temp-path.txt`) so subsequent tasks can find this directory. Bash variables don't persist between separate tool invocations.

```bash
echo "$TEMP" > /tmp/extract-temp-path.txt
```

- [ ] **Step 2: Filter to keep only `frontend/`**

```bash
cd "$TEMP/extracted"
git filter-repo --subdirectory-filter frontend
```

Expected output: filter-repo prints progress (parsing commits, rewriting refs). On success the working tree no longer contains `frontend/` as a subdirectory — its contents are now at the root.

If filter-repo errors with `Aborting: Refusing to destructively overwrite repo history since this does not look like a fresh clone`, that's normal protective behavior on the source repo — but we're operating on a clone, so it shouldn't trigger. If it does, STOP and surface; investigate before adding the `--force` flag.

- [ ] **Step 3: Verify the filtered tree looks right**

```bash
ls -la "$TEMP/extracted" | head -20
test -f "$TEMP/extracted/package.json" && echo "package.json OK"
test -d "$TEMP/extracted/src" && echo "src OK"
test -d "$TEMP/extracted/design_system" && echo "design_system OK"
test -f "$TEMP/extracted/next.config.ts" && echo "next.config.ts OK"
```

Expected: all four "OK" lines print. If any is missing, STOP — the filter took out something it shouldn't have.

- [ ] **Step 4: Verify history was preserved**

```bash
git -C "$TEMP/extracted" log --oneline | head -10
git -C "$TEMP/extracted" log --oneline | wc -l
```

Expected: a sensible number of commits (likely 10+), with messages that recognizably belong to the frontend (e.g. "feat(crm): ...", "Wipe frontend to rebuild from scratch", etc.). If the count is 0 or 1, the filter went wrong — STOP and surface.

- [ ] **Step 5: Verify there's no `origin` remote**

```bash
git -C "$TEMP/extracted" remote -v
```

Expected: empty output. (filter-repo strips remotes by default.) If `origin` is still listed, run `git -C "$TEMP/extracted" remote remove origin` and proceed.

No commit yet. No code change in either repo.

---

## Task 3: Move filtered clone into place

**Files:**
- Move: `$TEMP/extracted/` → `/Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend/`

- [ ] **Step 1: Confirm destination doesn't already exist**

```bash
test -e /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend && echo "EXISTS"
```

Expected: no output (path does not exist). If "EXISTS" prints, STOP — we'd be overwriting something. Surface to the user.

- [ ] **Step 2: Move the directory**

```bash
TEMP=$(cat /tmp/extract-temp-path.txt)
mv "$TEMP/extracted" /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend
```

- [ ] **Step 3: Verify the move**

```bash
ls /Users/giahuyhoangle/Projects/dental-system/ | sort
git -C /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend status
```

Expected (first command): `dental-crm-frontend` now appears alongside `dental-api`, `dental-agent`, etc.

Expected (second): "On branch main" (or whatever branch the dental-api clone was on at clone time — filter-repo doesn't change branch names; HEAD points at the filtered-equivalent of the source HEAD). Working tree clean.

- [ ] **Step 4: Confirm the parent /tmp dir is empty (we can leave it)**

```bash
ls -la "$TEMP" 2>/dev/null || echo "temp already cleaned"
```

The mktemp directory may still exist but be empty. Optional cleanup: `rm -rf "$TEMP"`. Skip if uncertain.

No commit on either side. (The new repo's history is the filtered history from filter-repo; no new commits yet.)

---

## Task 4: Copy `apphosting.yaml` into the new repo and commit

**Files:**
- Create: `dental-system/dental-crm-frontend/apphosting.yaml` (copy of `dental-api/apphosting.yaml`)

- [ ] **Step 1: Copy the file**

```bash
cp /Users/giahuyhoangle/Projects/dental-system/dental-api/apphosting.yaml \
   /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend/apphosting.yaml
```

- [ ] **Step 2: Verify it's identical**

```bash
diff /Users/giahuyhoangle/Projects/dental-system/dental-api/apphosting.yaml \
     /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend/apphosting.yaml
```

Expected: no output (files identical).

- [ ] **Step 3: Stage and commit in the new repo**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend
git add apphosting.yaml
git commit -m "chore: bring apphosting.yaml from dental-api at extraction time"
```

Expected: a new commit on top of the filtered history. `git log --oneline | head -3` should show this commit followed by the most recent frontend commit from the filtered history.

---

## Task 5: Smoke-test build in the new repo

**Files:** none (build artifacts only)

- [ ] **Step 1: Clean any stale build state**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend
rm -rf node_modules .next
```

Expected: no error (these may or may not exist).

- [ ] **Step 2: Install dependencies**

```bash
npm install 2>&1 | tail -20
```

Expected: completes without "ERROR" or "ELIFECYCLE" messages. Warnings are OK. A `node_modules/` directory now exists.

- [ ] **Step 3: Run a build**

```bash
npm run build 2>&1 | tail -30
```

Expected: the output ends with "✓ Compiled successfully" or similar Next.js success message, and the process exits with code 0.

**If the build fails, STOP. Do not proceed to Task 6 or later. The failure means the extraction isn't viable as-is — there's a file or config the old in-monorepo setup provided implicitly. Investigate by reading the error and surface to the user.**

Common failure modes:
- Missing TypeScript path mapping → check `tsconfig.json` paths section
- Missing peer dependency → check `package.json` peerDependencies vs installed
- Build-time env var unset → check `apphosting.yaml` env block; `npm run build` may need a `.env.local` (look for one in `frontend/` history)

No commit (build artifacts are gitignored).

---

## Task 6: Update `README.md` and `CLAUDE.md` in the new repo

**Files:**
- Modify: `dental-system/dental-crm-frontend/README.md`
- Modify: `dental-system/dental-crm-frontend/CLAUDE.md`

- [ ] **Step 1: Inspect current README**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend
cat README.md
```

Note any references to `dental-api/` paths or "part of the dental-api repo" — these are what we'll replace.

- [ ] **Step 2: Rewrite README to reflect standalone status**

Use the Edit tool (or rewrite the file). The new README should be brief and contain:

1. A one-line description: "CRM/PMS frontend for the Rocky Ridge dental clinic. Connects to the dental-api backend."
2. A "Setup" section:
   ```
   ## Setup

   ```bash
   npm install
   cp .env.local.example .env.local   # if an example exists
   npm run dev
   ```

   Opens http://localhost:3000 by default.
   ```
3. A "Backend" section:
   ```
   ## Backend

   This frontend talks to the dental-api backend (sibling repo: `dental-system/dental-api/`).
   The API base URL is configured via `NEXT_PUBLIC_API_BASE` in `.env.local` (development)
   or `apphosting.yaml` (production deploy on Firebase App Hosting).
   ```
4. Anything else from the old README that's still relevant (e.g. design system reference, Playwright test commands). Drop anything that referenced the old in-monorepo layout.

Keep it under 50 lines total.

- [ ] **Step 3: Inspect current CLAUDE.md**

```bash
cat CLAUDE.md
```

Note any references to `dental-api/` paths or "this is part of dental-api".

- [ ] **Step 4: Update CLAUDE.md**

Strip references to `dental-api/` paths. Keep the Design System guidance verbatim (that's frontend-specific and is the whole reason CLAUDE.md exists for this repo). Update any "ignore styling in frontend/src/" lines that now have no meaning — `src/` IS the source tree now, not "frontend/src". Adjust paths accordingly.

If CLAUDE.md mentions "`design_system/rockyridgeai-dental.com/`" or similar specific design-system folder paths, leave those unchanged — they refer to subdirectories that came with the extraction.

- [ ] **Step 5: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: update README and CLAUDE.md for standalone repo

README rewritten to reflect that this repo is now the canonical home of
the CRM/PMS frontend. CLAUDE.md scrubbed of dental-api/ path references;
Design System guidance preserved."
```

---

## Task 7: Verify state — both repos before destructive deletions

**Files:** none (verification only)

- [ ] **Step 1: Verify the new repo**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-crm-frontend
git log --oneline | head -5
ls -la | grep -E 'package.json|src|design_system|apphosting.yaml|README.md|CLAUDE.md' | head
```

Expected: recent commits include "chore: bring apphosting.yaml..." and "docs: update README and CLAUDE.md..."; the listed files all exist.

- [ ] **Step 2: Verify dental-api is unchanged**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
git status --porcelain | grep -v '^??' | head
```

Expected: empty (no tracked modifications). The dental-api working tree still has `frontend/`, `apphosting.yaml`, `dental-calendar/` — we haven't deleted them yet.

- [ ] **Step 3: Confirm npm build still succeeded**

This is just a re-check that we have a green signal before destruction. If Task 5 reported success, no action needed here. If you're uncertain, re-run `npm run build` in the new repo.

**Checkpoint:** if everything above is clean, the new repo is good. Proceeding to deletion in Task 8 is now low-risk because the new repo is a complete, building copy of what we're about to remove.

No commit.

---

## Task 8: Remove `frontend/`, `apphosting.yaml`, `dental-calendar/` from dental-api

**Files:**
- Delete from dental-api: `frontend/` (whole directory), `apphosting.yaml`, `dental-calendar/`

- [ ] **Step 1: Confirm `dental-calendar/` is empty**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
ls -la dental-calendar/
```

Expected: only `.` and `..`. If anything else is in there, STOP — surface to the user and ask what to do with the contents.

- [ ] **Step 2: `git rm` the tracked items**

```bash
git rm -r frontend/
git rm apphosting.yaml
```

Expected: git stages a large number of deletions (~all files inside frontend/) and one for apphosting.yaml. No errors.

- [ ] **Step 3: Remove the empty `dental-calendar/` directory**

`dental-calendar/` is empty so it's NOT tracked by git (git doesn't track empty directories). Just `rmdir` it on the filesystem.

```bash
rmdir dental-calendar/
```

Expected: succeeds silently. If `rmdir` errors with "Directory not empty", STOP — there's something in there.

- [ ] **Step 4: Verify**

```bash
test -e frontend && echo "frontend STILL EXISTS" || echo "frontend gone"
test -e apphosting.yaml && echo "apphosting.yaml STILL EXISTS" || echo "apphosting.yaml gone"
test -e dental-calendar && echo "dental-calendar STILL EXISTS" || echo "dental-calendar gone"
git status --short | head -10
```

Expected: three "gone" lines; `git status --short` shows many `D` (deleted) entries for frontend/ files plus `D apphosting.yaml`.

No commit yet — that happens in Task 10 along with the CLAUDE.md edit.

---

## Task 9: Strip Design System sections from `dental-api/CLAUDE.md`

**Files:**
- Modify: `dental-api/CLAUDE.md`

- [ ] **Step 1: Read the current CLAUDE.md to locate the sections to remove**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
grep -n "^## Design System\|frontend/\|Quick reference rules\|Ignore existing styling\|Ignore \`frontend" CLAUDE.md
```

Expected: line numbers for the Design System section header and the various "ignore frontend" mentions in the "Things to know" section.

- [ ] **Step 2: Remove the Design System block**

Find the line `## Design System (mandatory for all frontend/UI work)` and delete from that line through the line just before `## Things to know` (the next H2 heading). That's the "Design System" H2 plus the "rockyridge-dental-design" skill invocation block plus the "Quick reference rules" subsection.

Use the Edit tool with the exact old_string from the file (don't try to compute line numbers in commands).

- [ ] **Step 3: Remove the frontend-specific bullets in "Things to know"**

In the `## Things to know` section, delete these bullets:
- `- **Ignore existing styling in \`frontend/src/\`.**` (and the explanation that follows on the same bullet)
- `- **Ignore \`frontend/design_system/rockyridgeai.com/\` and \`frontend/design_system/dental-pms.v1/\`.**` (and the explanation)

Use the Edit tool. Match exact strings; if the bullets span multiple lines, include them in the old_string.

- [ ] **Step 4: Add a replacement pointer line**

In the `## Things to know` section, after the remaining bullets, add this one line:

```markdown
- The CRM/PMS frontend used to live at `frontend/`; it now lives in the sibling repo `dental-system/dental-crm-frontend/`.
```

- [ ] **Step 5: Verify CLAUDE.md is well-formed**

```bash
grep -c '^## ' CLAUDE.md
head -5 CLAUDE.md
```

Expected: at least 3 H2 headers remaining (LiveKit directives, Voice-AI research, Things to know), and `# CLAUDE.md` is still the first H1.

```bash
grep -nE 'frontend/src|frontend/design_system|rockyridge-dental-design' CLAUDE.md
```

Expected: empty (those references are all gone).

No commit yet. Task 10 commits everything together.

---

## Task 10: Commit the dental-api deletions + CLAUDE.md update

**Files:**
- Stage: `frontend/` deletions (already done by `git rm -r` in Task 8), `apphosting.yaml` deletion, modified `CLAUDE.md`

- [ ] **Step 1: Stage the CLAUDE.md change**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
git add CLAUDE.md
```

- [ ] **Step 2: Sanity-check what's staged**

```bash
git status --short | head -20
git diff --cached --stat | tail -10
```

Expected: many `D` entries for `frontend/...` files, one `D apphosting.yaml`, one `M CLAUDE.md`. The diff stat should show a large number of file deletions (hundreds, since frontend/ has many files) plus the small CLAUDE.md change. No additions, no other modifications.

If you see additions or unrelated modifications, STOP — something's off.

- [ ] **Step 3: Commit**

```bash
git commit -m "refactor: extract frontend into dental-crm-frontend sibling repo

Removes frontend/, apphosting.yaml, and the empty dental-calendar/ from
dental-api. The frontend now lives at dental-system/dental-crm-frontend/
with its own .git (history preserved via git filter-repo).

CLAUDE.md no longer carries the Design System section; that documentation
moved with the frontend code. Existing CORS allow-list entries for the
Firebase App Hosting URL remain — the frontend continues to deploy at the
same URL, only the source code location changed."
```

Expected: a single commit on `pms-frontend-overhaul` containing all the deletions + the CLAUDE.md edit.

- [ ] **Step 4: Verify**

```bash
git log --oneline -3
git show --stat HEAD | tail -5
```

Expected: the commit message above appears as HEAD; the stat shows a large number of deletions (hundreds) plus one modified file.

---

## Task 11: Verify dental-api tests still pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full pytest suite**

```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
.venv/bin/python -m pytest -q 2>&1 | tail -5
```

Expected: same passing count as before this refactor (post-Task-13 of the v1 refactor baseline was 286 passed). The API code wasn't touched in this work, so this should be a no-op verification.

If anything fails: STOP. Investigate. Possible causes:
- A test imports from `frontend/` somehow (unlikely but possible)
- A conftest.py or fixture referenced `apphosting.yaml`
- A test reads a file from `frontend/` (e.g. a snapshot or fixture)

Surface to the user with the specific failure. Do NOT roll back without their guidance — the deletion is recoverable via `git reset HEAD~1` or `git revert HEAD`.

- [ ] **Step 2: Final sanity check**

```bash
ls /Users/giahuyhoangle/Projects/dental-system/
ls /Users/giahuyhoangle/Projects/dental-system/dental-api/ | head -25
```

Expected (first): `dental-crm-frontend` now exists as a sibling of `dental-api`, `dental-agent`, etc.

Expected (second): no `frontend/`, no `apphosting.yaml`, no `dental-calendar/`. The dental-api repo is leaner.

```bash
wc -l /Users/giahuyhoangle/Projects/dental-system/dental-api/CLAUDE.md
```

Expected: meaningfully smaller than before the strip (was 104 lines; should now be ~60-70).

No commit. Reporting time.

---

## Done check

After Task 11:

- [ ] `dental-system/dental-crm-frontend/` exists as a new local repo with preserved git history.
- [ ] The new repo has its own `apphosting.yaml`, updated `README.md`, and updated `CLAUDE.md`.
- [ ] `npm install && npm run build` works in the new repo.
- [ ] `dental-api/` no longer contains `frontend/`, `apphosting.yaml`, or `dental-calendar/`.
- [ ] `dental-api/CLAUDE.md` no longer mentions `frontend/...` paths or the `rockyridge-dental-design` skill.
- [ ] `dental-api/` test suite still passes (`pytest -q` matches pre-task baseline).
- [ ] The pms-frontend-overhaul branch has one new commit on top of the v1 router refactor work, covering the dental-api side of the extraction.

## Out of scope (manual follow-ups, NOT part of this plan)

- Creating a GitHub repository for the new frontend (`gh repo create dental-crm-frontend && cd ... && git push -u origin main`).
- Re-pointing Firebase App Hosting to the new GitHub repository in the Firebase Console.
- Pruning frontend history out of `dental-api`'s own git log (would require destructive `git filter-repo --invert-paths --path frontend` on `dental-api`; explicitly out of scope per spec).
- Merging `pms-frontend-overhaul` into `main` (the user already declined this — branch is being kept as-is until they decide).

## Risk + mitigation summary

| Risk | Mitigation in plan |
|---|---|
| `git-filter-repo` not installed | Task 0 installs it |
| Hidden cross-boundary imports in `frontend/src/` | Task 1 Step 3 verifies; pre-design check found none |
| `apphosting.yaml` has path edits that need adjustment | Task 1 Step 4 verifies (file already inspected at design time — no edits needed) |
| Filter strips files it shouldn't | Task 2 Steps 3-4 verify by spot-checking key files + history |
| Destination dir already exists | Task 3 Step 1 checks before mv |
| `npm run build` fails | Task 5 Step 3 stops the plan before any deletion (Task 8); destructive operations only happen after the new repo is proven viable |
| `dental-calendar/` not actually empty | Task 8 Step 1 checks; surfaces if non-empty |
| dental-api tests regress | Task 11 verifies; rollback is `git reset HEAD~1` on dental-api |
| The two refactors (v1 router + frontend extraction) bundled in one branch surprise reviewers | Documented in the Task 10 commit message; user explicitly chose this layering |
