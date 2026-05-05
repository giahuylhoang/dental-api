#!/usr/bin/env bash
# Driver for the AI Receptionist prototype runbook.
#
# Behaviour:
# - For each task, dispatch kiro-cli with the assembled prompt, then run the
#   external test script (_tests/<id>.test.sh).
# - If the test passes: write _state/<id>.done.md, advance.
# - If the test fails: re-prompt kiro-cli with the test output and retry,
#   up to KIRO_MAX_RETRIES (default 5) total attempts per task.
# - If retries are exhausted: write _state/<id>.failed.md and CONTINUE to
#   the next task. Never halt the queue on a single task's failure.
#
# Tests are authoritative. Agent self-reports are ignored — only the test
# script decides pass/fail.
#
# Usage:
#   ./run.sh <task-id>          run one task with retries
#   ./run.sh --all              run every task in dependency order
#   ./run.sh --resume           skip tasks with a .done.md and run the rest
#   ./run.sh --list             list tasks + status
#   ./run.sh --dry <id>         print the assembled prompt only
#   ./run.sh --test <id>        run only the test (no kiro-cli)
#   ./run.sh --force <id>       delete state and rerun
#
# Env:
#   KIRO_MAX_RETRIES  default 5
#   KIRO_MODEL        default claude-opus-4.6

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNBOOK_DIR="$SCRIPT_DIR"
KIT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
STATE_DIR="$RUNBOOK_DIR/_state"
LOG_DIR="$RUNBOOK_DIR/_logs"
TEST_DIR="$RUNBOOK_DIR/_tests"
mkdir -p "$STATE_DIR" "$LOG_DIR"

MODEL="${KIRO_MODEL:-claude-opus-4.6}"
MAX_RETRIES="${KIRO_MAX_RETRIES:-5}"

ORDER=( "06A" "06B" "06C" "06D" "06E" "06F" "06G" "06H" "06I" "06J" "06K" "06L" )

# Parallelism cap when phases fan out.
PAR_MAX="${KIRO_PAR_MAX:-3}"

# Which shared-context file to inject for a given task id.
shared_for() {
  local id="$1"
  case "$id" in
    06*) echo "_shared-v3.md" ;;
    05*) echo "_shared-v2.md" ;;
    *)   echo "_shared.md"     ;;
  esac
}

# Which inventory file to point a given task id at.
inventory_for() {
  local id="$1"
  case "$id" in
    06*) echo "ui_kits/website/_prototype/INVENTORY-v4.md" ;;
    05*) echo "ui_kits/website/_prototype/INVENTORY-v3.md" ;;
    *)   echo "ui_kits/website/_prototype/INVENTORY.md"     ;;
  esac
}

resolve_prompt_file() {
  local id="$1"
  ls "$RUNBOOK_DIR"/${id}-*.md 2>/dev/null | head -n 1
}

assemble_prompt() {
  local prompt_file="$1" id="$2" extra="${3:-}"
  local shared_file inventory_path
  shared_file="$(shared_for "$id")"
  inventory_path="$(inventory_for "$id")"
  printf 'You are working inside the rockyridgeai-dental.com design system.\n'
  printf 'Working directory: %s\n' "$KIT_ROOT"
  printf 'Task ID: %s\n' "$id"
  printf 'Model: %s\n\n' "$MODEL"
  printf 'Read _runbook/%s before doing anything else. It is binding.\n' "$shared_file"
  printf 'Then read %s (ground truth for this round).\n' "$inventory_path"
  printf 'Then execute the task below. Write only the file(s) the task names. Do not modify any other file. Do not start any HTTP server.\n\n'
  printf 'The runbook driver runs an external test (ui_kits/website/_prototype/_runbook/_tests/%s.test.sh) after you finish. The test is authoritative. Self-reports are ignored — make the test pass.\n\n' "$id"
  printf 'You can run the test yourself before declaring done:\n'
  printf '    bash ui_kits/website/_prototype/_runbook/_tests/%s.test.sh\n\n' "$id"
  printf 'If a check fails, edit the file in place to satisfy it. Do not delete the file or rewrite from scratch unless absolutely necessary.\n\n'
  printf -- '------------------------- %s -------------------------\n' "$shared_file"
  cat "$RUNBOOK_DIR/$shared_file"
  printf '\n------------------------- %s -------------------------\n' "$(basename "$prompt_file")"
  cat "$prompt_file"
  if [[ -n "$extra" ]]; then
    printf '\n------------------------- retry context -------------------------\n%s\n' "$extra"
  fi
}

run_test() {
  local id="$1"
  local test_file="$TEST_DIR/${id}.test.sh"
  if [[ ! -f "$test_file" ]]; then
    echo "(no test for $id; treating as pass)"
    return 0
  fi
  cd "$KIT_ROOT"
  bash "$test_file"
}

write_done() {
  local id="$1" attempts="$2" log="$3"
  {
    printf '# Task %s — done\n\n' "$id"
    printf -- '- Attempts: %s\n' "$attempts"
    printf -- '- Test: _runbook/_tests/%s.test.sh PASSED\n' "$id"
    printf -- '- Last log: %s\n' "$log"
    printf -- '- Wallclock done: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
  } > "$STATE_DIR/${id}.done.md"
}

write_failed() {
  local id="$1" attempts="$2" log="$3" last_test_output="$4"
  {
    printf '# Task %s — FAILED after %s attempts\n\n' "$id" "$attempts"
    printf 'Test _runbook/_tests/%s.test.sh could not be made to pass within %s retries.\n\n' "$id" "$MAX_RETRIES"
    printf 'Last log: %s\n\n' "$log"
    printf 'Last test output:\n\n'
    printf '%s\n' "$last_test_output"
    printf '\nTo retry by hand:\n'
    printf '    bash %s/%s.test.sh\n' "$TEST_DIR" "$id"
    printf '    ./run.sh --force %s\n' "$id"
  } > "$STATE_DIR/${id}.failed.md"
}

build_retry_extra() {
  local id="$1" output="$2"
  printf 'Your previous attempt for task %s did not pass the external test.\n' "$id"
  printf 'The test runs from %s and lives at %s/%s.test.sh.\n\n' "$KIT_ROOT" "$TEST_DIR" "$id"
  printf 'Test output (full):\n\n'
  printf '%s\n\n' "$output"
  printf 'What to do:\n'
  printf '- Re-read the task body and _shared.md.\n'
  printf '- Inspect the file you wrote.\n'
  printf '- Edit the file in place so every FAIL line above becomes a PASS.\n'
  printf '- You can run the test yourself: bash %s/%s.test.sh from %s.\n' "$TEST_DIR" "$id" "$KIT_ROOT"
  printf '- Do not delete the existing file or modify anything outside the declared output paths.\n'
}

run_one() {
  local id="$1"
  local prompt_file
  prompt_file=$(resolve_prompt_file "$id")
  if [[ -z "$prompt_file" ]]; then
    echo "✗ $id: no prompt file matching ${id}-*.md" >&2
    return 1
  fi

  local extra=""
  local last_test_out=""
  local attempt
  for ((attempt=1; attempt<=MAX_RETRIES; attempt++)); do
    local ts; ts="$(date +%Y%m%d-%H%M%S)"
    local kiro_log="$LOG_DIR/${id}.attempt${attempt}.${ts}.kiro.log"
    local test_log="$LOG_DIR/${id}.attempt${attempt}.${ts}.test.log"

    echo
    echo "▶ $id attempt $attempt/$MAX_RETRIES (model: $MODEL)"
    echo "  prompt:    $(basename "$prompt_file")"
    echo "  kiro log:  $kiro_log"
    echo "  test log:  $test_log"

    cd "$KIT_ROOT"
    local prompt
    prompt=$(assemble_prompt "$prompt_file" "$id" "$extra")

    set +e
    kiro-cli chat --no-interactive --trust-all-tools --model "$MODEL" "$prompt" \
      >"$kiro_log" 2>&1
    local kiro_rc=$?
    set -e
    echo "  kiro-cli exit: $kiro_rc"

    set +e
    last_test_out=$(run_test "$id" 2>&1)
    local test_rc=$?
    set -e
    printf '%s\n' "$last_test_out" > "$test_log"
    echo "  test exit:     $test_rc"

    if [[ "$test_rc" -eq 0 ]]; then
      write_done "$id" "$attempt" "$kiro_log"
      echo "✔ $id passed on attempt $attempt"
      return 0
    fi

    extra=$(build_retry_extra "$id" "$last_test_out")
    extra="${extra}

This is attempt $((attempt + 1)) of $MAX_RETRIES."
  done

  echo "✗ $id: exhausted $MAX_RETRIES retries; recording failure and continuing."
  write_failed "$id" "$MAX_RETRIES" "$LOG_DIR/${id}.attempt${MAX_RETRIES}.*.kiro.log" "$last_test_out"
  return 0
}

cmd_list() {
  printf "%-6s  %-10s  %-10s  %s\n" "TASK" "STATUS" "TEST" "PROMPT"
  local id pf pf_label status test_label
  for id in "${ORDER[@]}"; do
    pf=$(resolve_prompt_file "$id")
    pf_label=$([[ -n "$pf" ]] && basename "$pf" || echo "(missing)")
    status="pending"
    [[ -f "$STATE_DIR/${id}.done.md"   ]] && status="done"
    [[ -f "$STATE_DIR/${id}.failed.md" ]] && status="failed"
    test_label="present"
    [[ -f "$TEST_DIR/${id}.test.sh" ]] || test_label="missing"
    printf "%-6s  %-10s  %-10s  %s\n" "$id" "$status" "$test_label" "$pf_label"
  done
}

cmd_dry() {
  local id="$1"
  local pf; pf=$(resolve_prompt_file "$id")
  assemble_prompt "$pf" "$id"
}

cmd_test_only() {
  local id="$1"
  cd "$KIT_ROOT"
  bash "$TEST_DIR/${id}.test.sh"
}

cmd_force() {
  local id="$1"
  rm -f "$STATE_DIR/${id}.done.md" "$STATE_DIR/${id}.failed.md"
  run_one "$id"
}

cmd_all() {
  local id
  for id in "${ORDER[@]}"; do
    if [[ -f "$STATE_DIR/${id}.done.md" ]]; then
      echo "↷ $id already done (state file present); skipping."
      continue
    fi
    rm -f "$STATE_DIR/${id}.failed.md"
    run_one "$id"
  done
  cmd_list
}

# cmd_par <id> <id> ...  — fan out up to PAR_MAX run_one calls in parallel,
# then wait. Per-task retry-until-pass is unchanged. Tasks already marked
# .done.md are skipped.
cmd_par() {
  local pids=()
  local n=0
  for id in "$@"; do
    if [[ -f "$STATE_DIR/${id}.done.md" ]]; then
      echo "↷ $id already done; skipping."
      continue
    fi
    rm -f "$STATE_DIR/${id}.failed.md"
    run_one "$id" &
    pids+=("$!")
    n=$((n + 1))
    if [[ $n -ge $PAR_MAX ]]; then
      wait
      pids=()
      n=0
    fi
  done
  if [[ ${#pids[@]} -gt 0 ]]; then
    wait
  fi
}

# cmd_v3 — orchestrate the 06* DAG with parallel fan-out where safe.
#   Phase 0: 06A
#   Phase 1: 06B            (sequential gate — branding sweep across 9 files)
#   Phase 2: 06C ‖ 06D ‖ 06E (data refactor + sidebar switcher + topbar profile)
#   Phase 3: 06F ‖ 06G ‖ 06H ‖ 06I (4 new config pages, all parallel-safe)
#   Phase 4: 06J            (kit Sidebar.jsx cross-link)
#   Phase 5: 06K            (AdminSidebar config-group expansion)
#   Phase 6: 06L            (E2E integrity)
cmd_v3() {
  echo "── Phase 0 — INVENTORY-v4 ──"
  cmd_par 06A
  echo
  echo "── Phase 1 — branding sweep (gate) ──"
  cmd_par 06B
  echo
  echo "── Phase 2 — data + chrome (3 parallel) ──"
  cmd_par 06C 06D 06E
  echo
  echo "── Phase 3 — 4 new config pages (parallel) ──"
  cmd_par 06F 06G 06H 06I
  echo
  echo "── Phase 4 — kit Sidebar cross-link ──"
  cmd_par 06J
  echo
  echo "── Phase 5 — AdminSidebar config-group expansion ──"
  cmd_par 06K
  echo
  echo "── Phase 6 — verify ──"
  cmd_par 06L
  echo
  cmd_list
}

# cmd_v2 — orchestrate the 05* DAG with parallel fan-out where safe.
#   Phase 0: 05A
#   Phase 1: 05B ‖ 05C ‖ 05D
#   Phase 2: 05E
#   Phase 3: 05F ‖ 05G
#   Phase 4: 05H → 05I → 05J → 05K   (same file; serialize)
#   Phase 5: 05L
#   Phase 6: 05M
cmd_v2() {
  echo "── Phase 0 — INVENTORY-v3 ──"
  cmd_par 05A
  echo
  echo "── Phase 1 — data layer (3 parallel) ──"
  cmd_par 05B 05C 05D
  echo
  echo "── Phase 2 — auth helpers ──"
  cmd_par 05E
  echo
  echo "── Phase 3 — chrome (2 parallel) ──"
  cmd_par 05F 05G
  echo
  echo "── Phase 4 — settings.html tabs (sequential, same file) ──"
  for id in 05H 05I 05J 05K; do
    if [[ -f "$STATE_DIR/${id}.done.md" ]]; then
      echo "↷ $id already done; skipping."
      continue
    fi
    rm -f "$STATE_DIR/${id}.failed.md"
    run_one "$id"
  done
  echo
  echo "── Phase 5 — login copy ──"
  cmd_par 05L
  echo
  echo "── Phase 6 — verify ──"
  cmd_par 05M
  echo
  cmd_list
}

main() {
  local arg="${1:-}"
  case "$arg" in
    ""|"-h"|"--help")
      sed -n '2,30p' "$0"
      ;;
    "--list")    cmd_list ;;
    "--all")     cmd_v3 ;;
    "--all-seq") cmd_all ;;
    "--v3")      cmd_v3 ;;
    "--v2")      cmd_v2 ;;
    "--resume")  cmd_v3 ;;
    "--par")     shift; cmd_par "$@" ;;
    "--dry")     cmd_dry "${2:?usage: --dry <task-id>}" ;;
    "--test")    cmd_test_only "${2:?usage: --test <task-id>}" ;;
    "--force")   cmd_force "${2:?usage: --force <task-id>}" ;;
    *)           run_one "$arg" ;;
  esac
}

main "$@"
