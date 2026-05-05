# Runbook — AI Receptionist admin prototype

Each Markdown file in this directory is a self-contained prompt for one prototype task. The driver `run.sh` concatenates `_shared.md` (binding context, voice rules, forbidden files) with the task prompt and dispatches the result to **kiro-cli (claude-opus-4.6, --no-interactive, --trust-all-tools)**.

## Status

```
./run.sh --list
```

## Run one task

```
./run.sh 02G          # writes admin-greeting.html
./run.sh 02A          # writes admin-dashboard.html
```

A task is considered green only when it writes `_state/<id>.done.md`. If that file is absent after kiro-cli exits, the driver treats the run as a failure and exits non-zero.

## Run the whole queue

```
./run.sh --all        # runs every pending task in dependency order
./run.sh --resume     # picks up at the first task without a done.md
```

The dependency order in `run.sh`'s `ORDER` array is:

```
02G  greeting
02A  dashboard          (uses mock; works against zero data; will look richer after 03B)
02B  calls
02C  call-detail
02D  patients
02E  schedule
03B  mock realism       (fills the data so dashboard/calls/schedule align)
03A  INDEX integration  (final wire-up)
03C  voice & empty-state pass
```

Why `03B` is queued *after* the page tasks: each page already handles empty data correctly (it's a success criterion). Filling the mock late means the page tasks can't accidentally hard-code values from the demo dataset — they must read the shape, not the contents.

## Inspect a prompt before running

```
./run.sh --dry 02C
```

This prints the assembled prompt (shared header + task body) to stdout without invoking kiro-cli. Useful for sanity-checking before spending credits.

## Logs and state

- `_logs/<id>.<timestamp>.log` — full kiro-cli stdout + stderr per run.
- `_state/<id>.done.md` — written by the task itself on success. Driver treats absence as failure.
- `_state/<id>.failed.md` — written by the task if it can't satisfy a success criterion (preferred over silent partial output).

## Smoke-test the prototype after a run

The kit is static HTML. Serve it from the kit root:

```
cd /Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com
python3 -m http.server 5180
open http://127.0.0.1:5180/ui_kits/website/_prototype/admin-routing.html
```

Verbatim-copy diff:

```
cd /Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com
for s in \
  "Welcome to … How can I help you today?" \
  "Both blank means closed that day." \
  "AI SIP URI (read-only here; engineer-managed)" \
  "First-time edits land as pending_review" \
  "Approve clinic (engineer-gated)" \
  "Recent calls and transcripts." \
  "CRM rollup from agent calls." \
  "Today's appointments (read-only)." \
  "Hours, holidays, transfer rules." \
  "Edit the AI greeting message."; do
  if grep -RFq "$s" ui_kits/website/_prototype/; then
    echo "OK  $s"
  else
    echo "MISS $s"
  fi
done
```

## Forbidden across all tasks

- Editing `login.html`, `Sidebar.jsx`, or any existing PMS page (`dashboard.html`, `patients.html`, `schedule.html`, `settings.html`, `lab.html`, etc.).
- Editing files outside `rockyridgeai-dental.com/`.
- Starting an HTTP server bound to all interfaces.
- Bringing in chart, audio, or React libraries beyond the kit's existing UMD CDN scripts.

These are repeated in `_shared.md` so each task gets them in-context.

## Changing the model

Override per-run:

```
KIRO_MODEL=claude-sonnet-4.6 ./run.sh 02E
```

Default is `claude-opus-4.6` to match the user's original spec.
