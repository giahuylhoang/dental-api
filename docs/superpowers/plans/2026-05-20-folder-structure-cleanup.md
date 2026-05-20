# Folder Structure Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tidy `dental-api/` after the v1 router refactor and frontend extraction — remove dead weight from git, declutter the root, refresh `CLAUDE.md` so it matches reality. **No `.py` code changes.**

**Architecture:** A janitor sweep done in 8 small commits (plus one local-only disk cleanup step). Each commit is independently reviewable and revertible. The only at-risk surface is `seed_db.sh` (was calling `./cloud-sql-proxy` from repo root); rewire it to resolve the binary from PATH.

**Tech Stack:** git, bash, FastAPI/pytest (verification only — no test changes).

---

## File Structure

### Files to be created

| Path | Responsibility |
|------|----------------|
| `scripts/deploy.sh` (moved from root, then gitignored — contains secrets) | Cloud Run deploy script |
| `scripts/provision_db.sh` (moved from root, tracked) | Cloud SQL instance provisioning |
| `scripts/seed_db.sh` (moved from root, tracked, edited) | Seed DB via cloud-sql-proxy |
| `scripts/smoke_tests.sh` (moved from root, tracked) | Post-deploy smoke tests |
| `.gcloudignore` (newly tracked from existing untracked file) | Build-exclusion config for `gcloud builds submit` |

### Files to be modified

| Path | Modification |
|------|--------------|
| `.gitignore` | Add missing patterns: `.DS_Store`, `.next/`, `.vercel/`, `node_modules/`, `cloud-sql-proxy`, gcloud dumps, Figma JSON exports, Claude transcripts, `scripts/deploy.sh` |
| `scripts/seed_db.sh` (after move) | Replace `./cloud-sql-proxy` with PATH-resolved invocation; fix the `cd` path |
| `DEPLOY_GOOGLE_CLOUD.md` | Update cloud-sql-proxy reference + point at `scripts/` paths |
| `CLAUDE.md` | Drop stale "empty services/" note; fix stale line refs; add repo-layout subsection |

### Files to be deleted

| Path | Reason |
|------|--------|
| `.DS_Store` (untracked from git, deleted from disk) | macOS noise |
| `.next/trace`, `.next/trace-build`, `.next/` dir | Old Next.js leftovers |
| `cloud-sql-proxy` (untracked from git, kept on disk locally) | 32 MB binary, install via gcloud instead |
| `2026-05-04-203049-this-session-is-being-continued-from-a-previous-c.txt` | Claude transcript |
| `database/__pycache__/*.pyc` (untracked from git, regenerated on next run) | Pre-gitignore pycache leftovers |
| `tmp/` (on-disk only, gitignored) | 1.1 GB legacy archive |
| `node_modules/`, `.vercel/` (on-disk only) | Frontend-era leftovers |
| `builds.json`, `status-*.json`, `dental-api-current.yaml` | gcloud command output dumps |
| `dental-dashboard-prototype.json`, `patient_prototype.json`, `pms-frontend-overhaul.json` | Figma JSON exports |
| Root copies of `deploy.sh`, `provision_db.sh`, `seed_db.sh`, `smoke_tests.sh` | Moved into `scripts/` |

---

## Task 0: Confirm starting state

**Files:**
- None modified

- [ ] **Step 1: Verify branch and clean baseline**

Run:
```bash
cd /Users/giahuyhoangle/Projects/dental-system/dental-api
git branch --show-current
git log --oneline -3
```

Expected:
- Branch: `pms-frontend-overhaul`
- Latest commit: `c89354e docs: folder-structure cleanup design spec`

- [ ] **Step 2: Snapshot the test baseline**

Run:
```bash
.venv/bin/python -m pytest -q 2>&1 | tail -5
```

Expected: `286 passed` (matches post-refactor baseline). If it doesn't, **STOP** — investigate before continuing. The cleanup must not change test results.

---

## Task 1: Untrack noise files from git

**Files:**
- Modify (git index only): `.DS_Store`, `.next/trace`, `.next/trace-build`, `cloud-sql-proxy`, `database/__pycache__/connection.cpython-312.pyc`, `database/__pycache__/models.cpython-312.pyc`
- Delete: `2026-05-04-203049-this-session-is-being-continued-from-a-previous-c.txt`

- [ ] **Step 1: Untrack files that should remain on disk**

Run:
```bash
git rm --cached .DS_Store
git rm --cached .next/trace .next/trace-build
git rm --cached cloud-sql-proxy
git rm -r --cached database/__pycache__
```

Expected output: each command lists `rm '<path>'`. The files stay on disk (verify with `ls -la .DS_Store cloud-sql-proxy`).

- [ ] **Step 2: Delete the Claude session transcript**

Run:
```bash
git rm 2026-05-04-203049-this-session-is-being-continued-from-a-previous-c.txt
```

Expected: `rm '2026-05-04-203049-this-session-is-being-continued-from-a-previous-c.txt'`. This one is removed from disk too (it's a transcript, no reason to keep it).

- [ ] **Step 3: Verify git status reflects only the intended changes**

Run:
```bash
git status --short
```

Expected: lines starting with `D` (deletion) for each of the six paths above, and nothing else surprising. The `database/__pycache__/*.pyc` lines that previously showed as ` M` (modified) should now show as `D` (staged deletion).

- [ ] **Step 4: Commit**

Run:
```bash
git commit -m "$(cat <<'EOF'
chore: untrack OS/build noise and committed binary

- Untrack .DS_Store (macOS noise) — kept on disk
- Untrack .next/trace, .next/trace-build (Next.js leftovers from when
  frontend lived here) — kept on disk
- Untrack cloud-sql-proxy (32 MB binary) — install via
  `gcloud components install cloud-sql-proxy` instead. Kept on disk
  locally as a convenience.
- Untrack database/__pycache__/*.pyc (predates the __pycache__/ rule)
- Delete the Claude Code session transcript from May 2026

.gitignore additions to lock these patterns in land in the next commit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds. The repo is now 32 MB lighter.

---

## Task 2: Update `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Append new patterns to `.gitignore`**

Append the block below to the existing `.gitignore` (do NOT remove or reorder existing lines):

```
# --- Added by post-refactor cleanup (2026-05-20) ---

# Editor / OS noise
.DS_Store
**/.DS_Store

# Old Next.js / Vercel leftovers (frontend moved to dental-crm-frontend)
.next/
node_modules/

# Local binaries — install via gcloud components instead
cloud-sql-proxy

# gcloud command outputs (regenerate as needed)
builds.json
status-*.json
dental-api-current.yaml

# Figma JSON exports (re-export from Figma if needed)
*-prototype.json
pms-frontend-overhaul.json

# Claude Code session transcripts
*this-session-is-being-continued*.txt

# Local-only deploy script (contains secrets — move to Secret Manager)
scripts/deploy.sh
```

Notes:
- `.vercel` is already covered by the existing `.vercel` line at the top.
- `tmp/`, `*.log`, `*.py[cod]`, `__pycache__/`, `logs/`, `var/` are already there.

- [ ] **Step 2: Verify the patterns work**

Run:
```bash
git check-ignore -v .DS_Store .next/trace cloud-sql-proxy builds.json status-api.json dental-api-current.yaml patient_prototype.json pms-frontend-overhaul.json 2>&1
```

Expected: each path matches a rule in `.gitignore` (one line per path).

- [ ] **Step 3: Commit**

Run:
```bash
git add .gitignore
git commit -m "$(cat <<'EOF'
chore: gitignore OS/build/dump/transcript patterns

Adds patterns to lock in the untracking done in the previous commit:
.DS_Store, .next/, node_modules/, cloud-sql-proxy, gcloud command
dumps, Figma JSON exports, Claude session transcripts.

Also gitignores scripts/deploy.sh, which contains Twilio secrets
(separate follow-up: move those to Secret Manager).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds.

---

## Task 3: Track `.gcloudignore`

**Files:**
- Add: `.gcloudignore` (already exists on disk; becomes tracked)

- [ ] **Step 1: Inspect the file before tracking**

Run:
```bash
cat .gcloudignore
```

Expected: a short file listing exclusions for `gcloud builds submit`. Make sure it contains no secrets. If it does, **STOP** and surface to the user.

- [ ] **Step 2: Track and commit**

Run:
```bash
git add .gcloudignore
git commit -m "$(cat <<'EOF'
chore: track .gcloudignore

This file controls what `gcloud builds submit` uploads; it should be
version-controlled alongside Dockerfile and the deploy scripts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds with `.gcloudignore` as the only added file.

---

## Task 4: Move shell scripts into `scripts/`

**Files:**
- Move: `provision_db.sh` → `scripts/provision_db.sh`
- Move: `seed_db.sh` → `scripts/seed_db.sh`
- Move: `smoke_tests.sh` → `scripts/smoke_tests.sh`
- Move: `deploy.sh` → `scripts/deploy.sh` (will be gitignored by previous task)
- Modify: `scripts/seed_db.sh` (cd path + cloud-sql-proxy reference)

- [ ] **Step 1: Move three commit-safe scripts into `scripts/`**

Run:
```bash
mv provision_db.sh scripts/provision_db.sh
mv seed_db.sh scripts/seed_db.sh
mv smoke_tests.sh scripts/smoke_tests.sh
chmod +x scripts/provision_db.sh scripts/seed_db.sh scripts/smoke_tests.sh
```

Expected: no output. Verify with `ls -la scripts/{provision_db,seed_db,smoke_tests}.sh`.

- [ ] **Step 2: Move `deploy.sh` (will not be committed — gitignored)**

Run:
```bash
mv deploy.sh scripts/deploy.sh
chmod +x scripts/deploy.sh
```

Expected: file moved. `git status --short` should NOT list `scripts/deploy.sh` because the `.gitignore` rule from Task 2 excludes it.

- [ ] **Step 3: Edit `scripts/seed_db.sh` — fix `cd` path and proxy invocation**

The current file starts:
```bash
#!/bin/bash
set -e

cd /Users/giahuyhoangle/Projects/dental-api

CONNECTION_NAME=$(cat /tmp/conn_name)
APP_PASSWORD=$(cat /tmp/app_pwd)
TOKEN=$(gcloud auth print-access-token)

echo "Starting cloud-sql-proxy..."
./cloud-sql-proxy "$CONNECTION_NAME" --port=5433 --token "$TOKEN" &
PROXY_PID=$!
```

Replace those lines with:
```bash
#!/bin/bash
set -e

# Resolve repo root from this script's location so the script works
# regardless of CWD or absolute-path drift across machines.
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

CONNECTION_NAME=$(cat /tmp/conn_name)
APP_PASSWORD=$(cat /tmp/app_pwd)
TOKEN=$(gcloud auth print-access-token)

# Resolve cloud-sql-proxy: prefer PATH (gcloud components install),
# fall back to a repo-root copy for backwards compatibility.
if command -v cloud-sql-proxy >/dev/null 2>&1; then
  PROXY_BIN="cloud-sql-proxy"
elif [ -x "./cloud-sql-proxy" ]; then
  PROXY_BIN="./cloud-sql-proxy"
else
  echo "ERROR: cloud-sql-proxy not found. Install via:" >&2
  echo "  gcloud components install cloud-sql-proxy" >&2
  exit 1
fi

echo "Starting cloud-sql-proxy via $PROXY_BIN..."
"$PROXY_BIN" "$CONNECTION_NAME" --port=5433 --token "$TOKEN" &
PROXY_PID=$!
```

Leave the rest of the file (waiting for proxy, running `sync_db.py`, killing proxy) unchanged.

- [ ] **Step 4: Verify the edit**

Run:
```bash
head -25 scripts/seed_db.sh
```

Expected: shows the new `SCRIPT_DIR` resolution and the `PROXY_BIN` block. The old `cd /Users/giahuyhoangle/Projects/dental-api` line is gone.

- [ ] **Step 5: Verify shell syntax**

Run:
```bash
bash -n scripts/provision_db.sh
bash -n scripts/seed_db.sh
bash -n scripts/smoke_tests.sh
```

Expected: no output for any of the three (exit code 0 = syntax OK). If any fail, fix before continuing.

- [ ] **Step 6: Commit the three tracked scripts**

Run:
```bash
git add scripts/provision_db.sh scripts/seed_db.sh scripts/smoke_tests.sh
git status --short
```

Expected: three new files staged; no other surprises. `scripts/deploy.sh` should NOT appear (it's gitignored).

```bash
git commit -m "$(cat <<'EOF'
chore: move operational shell scripts into scripts/

- provision_db.sh → scripts/provision_db.sh
- seed_db.sh     → scripts/seed_db.sh (cloud-sql-proxy now resolved via
                    PATH; cd uses BASH_SOURCE so the script works from
                    any CWD)
- smoke_tests.sh → scripts/smoke_tests.sh

deploy.sh is also moved to scripts/ but kept gitignored — it contains
hardcoded Twilio credentials. Separate follow-up: move those to
Secret Manager and commit a sanitized deploy.sh.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds.

---

## Task 5: Update `DEPLOY_GOOGLE_CLOUD.md`

**Files:**
- Modify: `DEPLOY_GOOGLE_CLOUD.md`

- [ ] **Step 1: Read the existing cloud-sql-proxy section**

Run:
```bash
grep -n "cloud-sql-proxy\|provision_db\|seed_db\|deploy.sh\|smoke_tests" DEPLOY_GOOGLE_CLOUD.md
```

Note the line numbers — you'll edit those.

- [ ] **Step 2: Update the cloud-sql-proxy install instruction**

Find the current line in `DEPLOY_GOOGLE_CLOUD.md`:

```markdown
1. [Install Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy#install)
2. Run: `cloud-sql-proxy YOUR_PROJECT_ID:us-central1:dental-api-db --port=5432`
```

Replace with:

```markdown
1. Install the proxy via gcloud:
   ```bash
   gcloud components install cloud-sql-proxy
   ```
   (Or download a binary from the [official docs](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy#install).)
2. Run: `cloud-sql-proxy YOUR_PROJECT_ID:us-central1:dental-api-db --port=5432`
```

Use the Edit tool with the exact `old_string` / `new_string` shown above.

- [ ] **Step 3: Add a "Operational scripts" section near the bottom of the file**

Find a stable anchor near the end of the file (after the last `##` heading) and append:

```markdown

## Operational scripts

All under `scripts/`:

- `scripts/provision_db.sh` — one-time Cloud SQL instance provisioning. Writes the connection name and app password to `/tmp/conn_name` and `/tmp/app_pwd`.
- `scripts/seed_db.sh` — starts `cloud-sql-proxy`, runs `scripts/sync_db.py` to create tables + seed defaults, then kills the proxy. Resolves the proxy from PATH (or a local `./cloud-sql-proxy` fallback).
- `scripts/smoke_tests.sh` — post-deploy curls against `/health`, `/api/doctors`, `/api/clinic`, SSE stream, end-to-end booking. Uses the current Cloud Run service URL.
- `scripts/deploy.sh` — Cloud Run deploy (gitignored locally because it currently hardcodes Twilio credentials; treat as a personal copy until those move to Secret Manager).
```

- [ ] **Step 4: Verify the file still renders sensibly**

Run:
```bash
wc -l DEPLOY_GOOGLE_CLOUD.md
head -90 DEPLOY_GOOGLE_CLOUD.md | tail -25
```

Confirm the proxy install block looks right.

- [ ] **Step 5: Commit**

Run:
```bash
git add DEPLOY_GOOGLE_CLOUD.md
git commit -m "$(cat <<'EOF'
docs: refresh deploy doc — cloud-sql-proxy via gcloud, scripts/ paths

- Install cloud-sql-proxy via `gcloud components install` (no longer
  shipped as a 32 MB binary in the repo).
- Add an "Operational scripts" section pointing at scripts/{provision,
  seed,smoke,deploy}_db.sh.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds.

---

## Task 6: Refresh `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

The current file has three stale claims that this task corrects. It also gets a short repo-layout subsection so contributors can navigate without grep.

- [ ] **Step 1: Fix the stale `get_clinic` reference**

In `CLAUDE.md`, the line:

```
This is enforced by the `get_clinic` dependency (`api/main.py:43`), which 404s if the clinic row doesn't exist.
```

Replace with:

```
This is enforced by the `get_clinic` dependency (`api/dependencies.py`), which 404s if the clinic row doesn't exist.
```

- [ ] **Step 2: Fix the stale conflict-detection line references**

Find:

```
The same "active statuses" set is used for conflict detection in create/reschedule (`api/main.py:319`, `api/main.py:916`). When changing status semantics, update both the slot computation and the conflict checks together.
```

Replace with:

```
The same "active statuses" set is used for conflict detection in `services/appointments.check_conflicts_for_create` and `check_conflicts_for_reschedule`. When changing status semantics, update both the slot computation and the conflict checks together.
```

- [ ] **Step 3: Rewrite the stale "empty services/" bullet**

Find:

```
- The empty `services/` directory is a leftover; business logic currently lives in `api/main.py` and `tools/`.
```

Replace with:

```
- Business logic lives in `services/` (`appointments.py`, `notifications.py`, `slots.py`). `api/v1/<domain>/router.py` modules are thin HTTP layers that delegate to `services/`; `api/main.py` is now just the FastAPI app + middleware + router mounts (~190 lines).
```

- [ ] **Step 4: Add a short "Repo layout" subsection just before "Things to know"**

Find the line starting with `## Things to know` and insert this block immediately above it (with a blank line separating):

```markdown
## Repo layout

- `api/` — FastAPI app (`main.py`), shared deps (`dependencies.py`), serializers, middleware, and per-version routers under `api/v1/<domain>/` and `api/v2/<track>/`.
- `services/` — business logic that v1 routers delegate to (appointments conflict checks, notifications, slot wrappers).
- `database/` — SQLAlchemy models, connection, observability hooks, and per-track sub-packages (`auth/`, `clinical/`, `ops/`).
- `clients/` — external-service adapters (Twilio SMS, SMTP email, lab case numbering).
- `tools/` — `slot_utils.py` (the actual slot computation; `services/slots.py` is a thin wrapper).
- `alembic/` — schema migrations. `versions/316d68e5e670_baseline_v1_schema.py` is the baseline; pre-baseline migrations under `scripts/migrate_*.py` are kept for historical reference but should not be re-run on greenfield databases.
- `scripts/` — operational shells (`provision_db.sh`, `seed_db.sh`, `smoke_tests.sh`, gitignored `deploy.sh`), schema sync (`sync_db.py`), seed scripts (`seed_*.py`), and historical pre-baseline migrations.
- `tests/` — pytest suite (286 passing). Uses in-memory SQLite via `tests/conftest.py`.
- `docs/superpowers/` — design specs and implementation plans for refactors.

```

- [ ] **Step 5: Verify CLAUDE.md is still under 100 lines**

Run:
```bash
wc -l CLAUDE.md
```

Expected: ≤ 100 lines. The original was 79 lines; the layout subsection adds ~12, the three stale-line edits are net-neutral.

If over 100, trim the layout subsection's verbose bits (cut sub-bullets, keep one sentence per directory).

- [ ] **Step 6: Commit**

Run:
```bash
git add CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(claude.md): refresh for post-refactor reality

- Fix stale "empty services/" claim — services/ now holds the
  appointments / notifications / slots business-logic split.
- Update line references in api/main.py to the post-refactor homes
  (api/dependencies.py, services/appointments.py).
- Add a "Repo layout" subsection so contributors don't have to grep
  to learn where things live.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds.

---

## Task 7: Delete on-disk clutter (no commit)

**Files:**
- Delete (local disk only): `tmp/`, `node_modules/`, `.vercel/`, `.next/`, `builds.json`, `status-*.json`, `dental-api-current.yaml`, `dental-dashboard-prototype.json`, `patient_prototype.json`, `pms-frontend-overhaul.json`

None of these are tracked (after Task 1 + Task 2) — this step just frees disk space and tidies the working tree.

- [ ] **Step 1: Sanity-check what gets deleted**

Run:
```bash
ls -la tmp 2>/dev/null | head -3
du -sh tmp node_modules .vercel .next 2>/dev/null
ls -la builds.json status-*.json dental-api-current.yaml dental-dashboard-prototype.json patient_prototype.json pms-frontend-overhaul.json 2>/dev/null
```

This is the destructive list. Read it before running step 2.

- [ ] **Step 2: Confirm none of these are tracked**

Run:
```bash
git ls-files tmp node_modules .vercel .next builds.json status-api.json status-crm.json status-crm-new.json status-crm-final.json dental-api-current.yaml dental-dashboard-prototype.json patient_prototype.json pms-frontend-overhaul.json 2>/dev/null | head
```

Expected: empty output. If anything appears, **STOP** — that file is tracked and must be `git rm`'d via Task 1 instead.

- [ ] **Step 3: Delete the gcloud / Figma JSON dumps and the YAML**

Run:
```bash
rm -f builds.json status-api.json status-crm.json status-crm-new.json status-crm-final.json dental-api-current.yaml dental-dashboard-prototype.json patient_prototype.json pms-frontend-overhaul.json
```

Expected: no output.

- [ ] **Step 4: Delete the legacy directories**

Run:
```bash
rm -rf tmp node_modules .vercel .next
```

Expected: no output. (`tmp/` will take a moment — 1.1 GB.)

- [ ] **Step 5: Verify nothing tracked was touched**

Run:
```bash
git status --short
```

Expected: clean — nothing modified, nothing staged. If `git status` shows anything, **STOP** and investigate before proceeding.

No commit. This step is intentionally a local-only disk cleanup.

---

## Task 8: Final verification

**Files:**
- None modified

- [ ] **Step 1: Run the test suite**

Run:
```bash
.venv/bin/python -m pytest -q 2>&1 | tail -5
```

Expected: `286 passed` (same as Task 0 baseline). If any test fails, **STOP** — diagnose before declaring done. None of the cleanup should have moved a `.py` file.

- [ ] **Step 2: Confirm the repo root is tidy**

Run:
```bash
ls -1 | sort
```

Expected output (exact set; some hidden dirs like `.venv`, `.git` will also appear but are gitignored):

```
.dockerignore
.env.example
.gcloudignore
.gitignore
2026-05-04-...     # SHOULD NOT BE PRESENT
CLAUDE.md
DEPLOY_GOOGLE_CLOUD.md
Dockerfile
Makefile
README.md
alembic
alembic.ini
api
clients
cloud-sql-proxy    # kept on disk (untracked)
database
dental_clinic.db
docs
node_modules       # SHOULD NOT BE PRESENT
patient_prototype.json   # SHOULD NOT BE PRESENT
pyproject.toml
requirements-dev.txt
requirements.txt
run_api.py
run_local.sh
scripts
services
tests
tmp                # SHOULD NOT BE PRESENT
tools
uv.lock
```

The marked rows must NOT appear. If any do, find the task they should have been cleaned in and fix it.

- [ ] **Step 3: Confirm git status is clean**

Run:
```bash
git status --short
```

Expected: empty output (or only lines for `.venv/`, `logs/`, `var/`, etc. — paths already gitignored that produce informational `??` lines should be invisible because of the existing rules).

If anything unexpected shows, investigate.

- [ ] **Step 4: Confirm new layout in docs is accurate**

Run:
```bash
sed -n '/^## Repo layout/,/^## /p' CLAUDE.md | head -20
```

Expected: the repo-layout subsection added in Task 6 appears intact.

- [ ] **Step 5: Final summary commit** (optional housekeeping)

If the prior commits all landed cleanly, no further commit is needed. Skip this step unless something needs reconciling.

- [ ] **Step 6: Report completion**

Summary to surface to the user:

```
Folder structure cleanup complete on pms-frontend-overhaul.

Commits added (in order):
  c89354e docs: folder-structure cleanup design spec  [prior]
  <T1>    chore: untrack OS/build noise and committed binary
  <T2>    chore: gitignore OS/build/dump/transcript patterns
  <T3>    chore: track .gcloudignore
  <T4>    chore: move operational shell scripts into scripts/
  <T5>    docs: refresh deploy doc — cloud-sql-proxy via gcloud, scripts/ paths
  <T6>    docs(claude.md): refresh for post-refactor reality

Local-only changes (no commit):
  - Deleted tmp/ (1.1 GB), node_modules/, .vercel/, .next/
  - Deleted root gcloud dumps and Figma JSON exports

Tests: 286 passed (no regression).

Follow-ups flagged but not done:
  - scripts/deploy.sh still hardcodes Twilio creds; move to Secret Manager.
```

---

## Self-review

**1. Spec coverage:**

| Spec item | Task |
|-----------|------|
| Untrack `.DS_Store`, `.next/trace*`, `cloud-sql-proxy`, transcript, pycaches | Task 1 |
| Delete tmp/, node_modules/, .vercel/, .next/, JSON/YAML dumps from disk | Task 7 |
| Move 4 shell scripts to `scripts/` + edit seed_db.sh | Task 4 |
| Track `.gcloudignore` | Task 3 |
| Update `.gitignore` | Task 2 |
| Update `DEPLOY_GOOGLE_CLOUD.md` for proxy install | Task 5 |
| Refresh `CLAUDE.md` (3 stale lines + repo-layout subsection) | Task 6 |
| `pytest -q` passes after | Task 0 + Task 8 |
| `ls` at root tidy | Task 8 |

All spec items covered.

**2. Placeholder scan:** Plan has no "TBD", "TODO" in steps, no "similar to" cross-refs, no generic "add error handling" — every step shows the actual commands or file contents.

**3. Type / name consistency:** No types in this plan; just file paths and shell commands. Paths consistent throughout (`scripts/seed_db.sh`, `services/appointments.check_conflicts_for_create`, etc.).

**4. Deviation from spec:** Spec said track all four moved scripts; plan diverges by gitignoring `scripts/deploy.sh` because it contains real Twilio creds. Documented in Task 4 commit message and in spec via Task 6 follow-up.
