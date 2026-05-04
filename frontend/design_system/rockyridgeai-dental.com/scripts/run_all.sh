#!/usr/bin/env bash
# Run all six phases in order. Short-circuit on first failure.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for phase in 1 2 3 4 5 6; do
  if ! "$ROOT/scripts/run_phase.sh" "$phase"; then
    echo "==> Aborting at phase $phase" >&2
    exit 1
  fi
done
echo "==> All phases passed"
