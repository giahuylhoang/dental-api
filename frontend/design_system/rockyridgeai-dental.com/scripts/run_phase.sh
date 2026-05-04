#!/usr/bin/env bash
# Driver: invoke kiro-cli to execute one phase of the static-site build.
# Usage: scripts/run_phase.sh <phase_number>
set -euo pipefail

PHASE="${1:?usage: run_phase.sh <phase_number>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SPEC="$ROOT/scripts/phase_${PHASE}_spec.md"
TEST="$ROOT/scripts/test_phase${PHASE}.sh"
LOGDIR="$ROOT/logs"
MAX_ATTEMPTS=3
MODEL="claude-sonnet-4.6"

mkdir -p "$LOGDIR"

if [[ ! -f "$SPEC" ]]; then
  echo "Missing spec: $SPEC" >&2
  exit 2
fi
if [[ ! -x "$TEST" ]]; then
  echo "Missing or non-executable test: $TEST" >&2
  exit 2
fi

cd "$ROOT"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  log="$LOGDIR/phase${PHASE}_attempt${attempt}.log"
  echo "==> Phase $PHASE attempt $attempt — kiro-cli ($MODEL)"
  echo "    spec: $SPEC"
  echo "    log:  $log"

  prompt="Execute the phase spec at $SPEC. Read it fully, then make the file edits it describes. After editing, run $TEST and report whether it passed. If it failed, fix the issues and re-run until it passes or you run out of turns. The working directory is $ROOT. All file paths in the spec are relative to that directory unless otherwise noted."

  if [[ $attempt -gt 1 ]]; then
    prev="$LOGDIR/phase${PHASE}_attempt$((attempt-1)).log"
    prompt+=$'\n\nThe previous attempt failed. Tail of previous log:\n'
    prompt+="$(tail -120 "$prev" 2>/dev/null || true)"
  fi

  kiro-cli chat \
    --model "$MODEL" \
    --trust-all-tools \
    --no-interactive \
    "$prompt" 2>&1 | tee "$log" || true

  if bash "$TEST"; then
    echo "==> Phase $PHASE PASSED on attempt $attempt"
    exit 0
  fi

  echo "==> Phase $PHASE FAILED attempt $attempt"
done

echo "==> Phase $PHASE failed after $MAX_ATTEMPTS attempts" >&2
exit 1
