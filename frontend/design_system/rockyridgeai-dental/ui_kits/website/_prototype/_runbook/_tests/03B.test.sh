#!/usr/bin/env bash
# Test for Task 03B — admin_mock.js realism pass
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_lib.sh"

F="data/admin_mock.js"

assert_file_exists "$F"
assert_file_size   "$F" 8000 200000

# Clinic identity must remain
assert_contains "$F" "Northeast Denture Clinic"
assert_contains "$F" "northeast-denture-clinic"
assert_contains "$F" "America/Edmonton"
assert_contains "$F" "+15879738089"
assert_contains "$F" "+13682990959"
assert_contains "$F" "sip:34.130.210.160:5060"

# Required collections + invariants block
assert_contains "$F" "validateAdminMock"
assert_contains "$F" "ROUTING"
assert_contains "$F" "GREETING"
assert_contains "$F" "KPIS"
assert_contains "$F" "CALLS"
assert_contains "$F" "TRANSCRIPTS"
assert_contains "$F" "PATIENTS"
assert_contains "$F" "APPOINTMENTS"

# Coverage targets
# Patients (≥12 entries)
assert_grep_count "$F" "patient_id:" 12 200
# Calls (≥32 entries)
assert_grep_count "$F" "call_id:" 32 400
# Appointments (≥14 entries)
assert_grep_count "$F" "(\"|')apt_[a-z0-9]" 14 400

# Outcome distribution: at least 14 'booked'
assert_grep_count "$F" "outcome: ['\"]booked['\"]" 14 400

# Three transcripts
assert_grep_count "$F" "speaker:" 30 9999

# Run the file in node — validates syntax + the invariants block.
# Stub a minimal `window` so the IIFE executes; turn console.assert into a
# throwing assertion so test fails on invariant breaks.
node -e "
  global.window = {};
  global.console = console;
  global.console.assert = (cond, msg) => { if (!cond) { throw new Error('invariant: ' + msg); } };
  require('fs').readFileSync('$F','utf-8');
  require('vm').runInThisContext(require('fs').readFileSync('$F','utf-8'), { filename: '$F' });
  if (!global.window.ADMIN_MOCK) throw new Error('window.ADMIN_MOCK was not set');
  const m = global.window.ADMIN_MOCK;
  if (!Array.isArray(m.CALLS)) throw new Error('CALLS not array');
  if (!Array.isArray(m.PATIENTS)) throw new Error('PATIENTS not array');
  if (!Array.isArray(m.APPOINTMENTS)) throw new Error('APPOINTMENTS not array');
  console.log('node-load ADMIN_MOCK ok: calls=' + m.CALLS.length + ' patients=' + m.PATIENTS.length + ' appts=' + m.APPOINTMENTS.length);
" 2>&1 && ok "node-load + invariants" || bad "node-load or invariants failed"

test_summary
