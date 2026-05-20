#!/usr/bin/env bash
# Sequential runner for re-trying failed R-tasks one at a time
# (avoids next build cache contention).
set -uo pipefail
ORCH="/Users/giahuyhoangle/Projects/dental-api/scripts/run_pms_rebuild.sh"
fails=0
for t in "$@"; do
  echo "==> RUN $t (sequential)"
  if ! bash "$ORCH" "$t"; then
    fails=$((fails+1))
    echo "==> $t FAILED — continuing"
  fi
done
echo "==> SERIAL DONE — $fails failures"
exit "$fails"
