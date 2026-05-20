# Folder Structure Cleanup — Design Spec

**Date:** 2026-05-20
**Branch:** `pms-frontend-overhaul`
**Author:** session-driven, approved by user
**Status:** ready for plan

## Goal

Tidy `dental-api/` after the v1 router refactor and frontend extraction. Remove dead weight from git, declutter the repo root, and refresh `CLAUDE.md` so it matches the post-refactor reality. **No code logic changes.**

## Why this matters

The two recent refactors (v1 router split + frontend extraction) left the repo functionally clean but visually noisy:

- A 32 MB binary (`cloud-sql-proxy`) and an old Claude transcript are checked into git.
- The root directory mixes 21 tracked files with 13+ untracked clutter files (build outputs, status dumps, Figma JSON exports).
- `tmp/` holds 1.1 GB of archived old frontend / docs / scripts that the team is no longer supposed to touch.
- `CLAUDE.md` still claims `services/` is empty and points at line numbers in `api/main.py` that no longer exist.

A new contributor opening the repo today sees the mess before they see the structure. This is a cosmetic cleanup, but cosmetics dictate first impressions.

## Non-goals

- No renaming or moving of `api/v1/`, `api/v2/`, `services/`, `database/`, `clients/`, `tools/`, or `alembic/`. They were just refactored; the structure is fine.
- No code changes in any `.py` file under those directories.
- No deletion of `scripts/migrate_*.py` — they're pre-alembic-baseline historical scripts that `CLAUDE.md` actively references.
- No deletion of the tracked seed database `dental_clinic.db` — `CLAUDE.md` documents it as intentional.
- No new directories beyond what's needed; no new abstractions.

## What gets cleaned up

### 1. Files to untrack from git (`git rm --cached`)

| Path | Why | Replacement |
|------|-----|-------------|
| `.DS_Store` | macOS Finder noise. | `.gitignore` adds `.DS_Store` |
| `.next/trace`, `.next/trace-build` | Next.js build artifacts from when the frontend lived here. The whole `.next/` directory is dead. | `.gitignore` adds `.next/` |
| `cloud-sql-proxy` | 32 MB binary. Should be installed via `gcloud components install cloud-sql-proxy` (or downloaded ad-hoc). | `.gitignore` adds `cloud-sql-proxy`; `DEPLOY_GOOGLE_CLOUD.md` updated with install instructions; `seed_db.sh` updated to call the binary via `command -v cloud-sql-proxy` rather than `./cloud-sql-proxy` |
| `2026-05-04-203049-this-session-is-being-continued-from-a-previous-c.txt` | Claude Code session transcript. Does not belong in git. | Deleted |
| `database/__pycache__/*.pyc` | `__pycache__/` is gitignored but these `.pyc` files were tracked before the rule existed and the rule doesn't untrack already-tracked files. | None — also covered by `.gitignore` already |

All `git rm --cached` operations: the files remain on disk locally (for `.pyc`, regenerated on next run; for `cloud-sql-proxy`, kept as a local convenience).

### 2. Files to delete from disk (already untracked)

These are gcloud command outputs and exported Figma JSON the user can regenerate; they don't belong in version control or on a clean working tree.

| Path | Origin | Action |
|------|--------|--------|
| `builds.json` | `gcloud builds list --format=json` output | Delete |
| `status-api.json`, `status-crm.json`, `status-crm-new.json`, `status-crm-final.json` | `gcloud run services describe ... --format=json` outputs | Delete |
| `dental-api-current.yaml` | `gcloud run services describe ... --format=yaml` output | Delete |
| `dental-dashboard-prototype.json` (1.3 MB), `patient_prototype.json` (1.3 MB), `pms-frontend-overhaul.json` (845 KB) | Figma JSON exports — historical prototypes the user can re-export from Figma if needed | Delete |
| `tmp/` | 1.1 GB archive of legacy frontend / docs / scripts. CLAUDE.md already says "don't add new code there". The `.gitignore` covers it. | Delete from disk |
| `node_modules/` (4 KB), `.vercel/` (8 KB), `.next/` (8 KB after step 1) | Frontend-era leftovers | Delete from disk |
| `.pytest_cache/`, `.cursor/` (tracked but stale) | Editor / test cache | Leave alone — gitignored, regenerates |

### 3. Files to move

| From | To | Why |
|------|-----|-----|
| `deploy.sh` | `scripts/deploy.sh` | Operational script, belongs with other scripts |
| `provision_db.sh` | `scripts/provision_db.sh` | Same |
| `seed_db.sh` | `scripts/seed_db.sh` | Same — also update internal `./cloud-sql-proxy` reference to PATH-resolved binary |
| `smoke_tests.sh` | `scripts/smoke_tests.sh` | Same |

None of these are currently tracked. We **track them in their new location** (they're real operational scripts and should be in git going forward).

### 4. Files to track for the first time

| Path | Why |
|------|-----|
| `.gcloudignore` | Build-exclusion config used by `gcloud builds submit`. Currently untracked; should be tracked. |

### 5. `.gitignore` additions

Append a "post-refactor cleanup" block covering:

```
# Editor / OS noise
.DS_Store

# Old Next.js / Vercel leftovers (frontend moved to dental-crm-frontend)
.next/
.vercel/
node_modules/

# Local binaries (install via gcloud components)
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
```

Some patterns overlap with the existing `.gitignore` (which already has `.env.*`, `tmp/`, `__pycache__/`, `logs/`, `var/`). Don't duplicate — only add what's missing.

### 6. `CLAUDE.md` refresh

Stale lines to fix:

| Current text | Problem | Replacement |
|--------------|---------|-------------|
| "The empty `services/` directory is a leftover; business logic currently lives in `api/main.py` and `tools/`." | `services/` is no longer empty — it holds `appointments.py`, `notifications.py`, `slots.py` post-refactor. | Update to: "Business logic lives in `services/` (appointments, notifications, slot-availability wrappers). The v1 HTTP routes in `api/v1/<domain>/router.py` are thin and delegate to `services/`." |
| "the `get_clinic` dependency (`api/main.py:43`)" | After refactor, `get_clinic` is in `api/dependencies.py`. | Update path to `api/dependencies.py`. |
| "conflict detection in create/reschedule (`api/main.py:319`, `api/main.py:916`)" | Conflict logic now lives in `services/appointments.py`. | Update to point at `services/appointments.check_conflicts_for_create` and `check_conflicts_for_reschedule`. |

Add a short **Repo layout** subsection just before the "Things to know" section, with one-sentence-per-directory summaries. This replaces having to grep around to learn the structure.

Keep CLAUDE.md under 100 lines.

### 7. Verification

After all changes:

- `pytest -q` passes (`286 passed`).
- `git status` shows clean working tree.
- `ls` at repo root shows: tracked source dirs + `alembic.ini`, `CLAUDE.md`, `DEPLOY_GOOGLE_CLOUD.md`, `Dockerfile`, `Makefile`, `README.md`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `run_api.py`, `run_local.sh`, `uv.lock`, `dental_clinic.db`, `.gitignore`, `.dockerignore`, `.env.example`, `.gcloudignore` — and no rogue JSON/YAML/SH/TXT files.

## Architecture / approach

This is a janitor sweep — file moves, untracking, gitignore edits, and one docs refresh. **Nothing in `.py` code changes.** No new files are introduced beyond the spec + plan documents.

The work is sequenced so each commit is independently reviewable and revertible:

1. Untrack the dead files (`git rm --cached` + `git rm` for the transcript).
2. Update `.gitignore` to lock the patterns in.
3. Move the four shell scripts to `scripts/`.
4. Track `.gcloudignore`.
5. Update `seed_db.sh` and `DEPLOY_GOOGLE_CLOUD.md` to handle the removed `cloud-sql-proxy` binary.
6. Refresh `CLAUDE.md`.
7. Delete on-disk clutter (`tmp/`, `node_modules/`, etc.) — local-only, no commit.
8. Run `pytest -q` as the final gate.

## Risk / blast radius

**Low.** The only at-risk surface is `seed_db.sh`, which currently calls `./cloud-sql-proxy`. After the move:

- The script lives at `scripts/seed_db.sh`.
- The binary is no longer at the repo root.
- The script must resolve the binary via PATH (post-`gcloud components install cloud-sql-proxy`).

If a developer ran the script with the binary still in their working tree, it'll keep working because the binary is gitignored, not deleted from disk. New developers will hit the install step documented in `DEPLOY_GOOGLE_CLOUD.md`.

Tests don't touch any of the moved files. The FastAPI app code is untouched.

## Decisions made without asking (per user's "no clarifying questions" instruction)

1. **Delete `tmp/` from disk.** It's 1.1 GB, gitignored, and `CLAUDE.md` says "don't add new code there". User said "delete" in the prompt.
2. **Delete the Figma prototype JSONs** rather than archiving them. They're re-exportable from Figma.
3. **Keep `dental_clinic.db` tracked.** `CLAUDE.md` documents it as intentional seed data.
4. **Keep all `scripts/migrate_*.py` and `scripts/seed_*.py`.** Pre-alembic-baseline but referenced in `CLAUDE.md`.
5. **Keep `cloud-sql-proxy` locally** (gitignored). Don't force a `rm` — user may want it on disk for convenience.
6. **No directory renames.** Cosmetic shuffling without function-level justification is churn.
7. **Inline execution recommended** over subagent-driven. This is file ops + a docs refresh; subagent overhead doesn't pay back.

## Out of scope (deferred)

- Pruning `scripts/migrate_*.py` historical migrations — needs a separate decision once we're confident the alembic baseline fully replaces them.
- Folding `tools/slot_utils.py` into `services/slots.py` — slot_utils is the implementation; services/slots is a thin wrapper. Keeping them split is fine.
- Re-organizing `clients/` (currently mixes `sms_client.py`, `email_client.py`, `lab_case_numbering.py` — the lab one is not a "client" in the same sense, but renaming `clients/` is bigger than cleanup).
- Removing `node_modules/` references from `pyproject.toml` or anywhere else — none exist; the directory is just an empty leftover.
