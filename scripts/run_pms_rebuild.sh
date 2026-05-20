#!/usr/bin/env bash
# Orchestrator for the PMS Next.js rebuild kiro-cli loop.
# Usage:
#   scripts/run_pms_rebuild.sh T01            # run a single task with retries
#   scripts/run_pms_rebuild.sh --parallel T03 T04 T05   # run multiple tasks concurrently
set -euo pipefail

ROOT="/Users/giahuyhoangle/Projects/dental-api"
SPEC_DIR="$ROOT/scripts/pms_rebuild"
LOG_DIR="$ROOT/logs/pms_rebuild"
MAX_ATTEMPTS=3
MODEL="claude-sonnet-4.6"
mkdir -p "$LOG_DIR"

run_task () {
  local task="$1"
  local spec="$SPEC_DIR/${task}_spec.md"
  local test_script="$SPEC_DIR/test_${task}.sh"

  if [[ ! -f "$spec" ]]; then
    echo "[$task] missing spec at $spec" >&2
    return 2
  fi
  if [[ ! -f "$test_script" ]]; then
    echo "[$task] missing test script at $test_script" >&2
    return 2
  fi

  for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
    local log="$LOG_DIR/${task}_attempt${attempt}.log"
    local prompt="You are executing task $task for the dental-api Next.js rebuild.
Read the full spec at: $spec
Working directory: $ROOT
After making the file edits the spec describes, run: bash $test_script
Iterate until the test script exits 0. Do NOT modify $ROOT/frontend/ — that is the legacy Vite app and stays untouched."
    if [[ $attempt -gt 1 ]]; then
      local prev="$LOG_DIR/${task}_attempt$((attempt-1)).log"
      prompt+=$'\n\nPrevious attempt failed. Tail of previous log (last 200 lines):\n'
      prompt+="$(tail -200 "$prev" 2>/dev/null || true)"
    fi
    echo "==> [$task] attempt $attempt"
    kiro-cli chat --model "$MODEL" --trust-all-tools --no-interactive "$prompt" 2>&1 \
      | tee "$log" || true
    if bash "$test_script"; then
      echo "==> [$task] PASSED on attempt $attempt"
      return 0
    fi
    echo "==> [$task] test failed on attempt $attempt"
  done
  echo "==> [$task] FAILED after $MAX_ATTEMPTS attempts" >&2
  return 1
}

if [[ "${1:-}" == "--parallel" ]]; then
  shift
  pids=()
  fails=0
  for t in "$@"; do
    ( run_task "$t" ) &
    pids+=($!)
  done
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      fails=$((fails+1))
    fi
  done
  exit "$fails"
fi

run_task "${1:?usage: run_pms_rebuild.sh <task_id> [...] | --parallel <task_id>...}"
