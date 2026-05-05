# Shared assertion helpers for runbook test scripts.
# Sourced by every <id>.test.sh. Each helper writes a single PASS/FAIL line
# and increments a counter. Test exits non-zero if any FAIL was recorded.

PASS_COUNT=0
FAIL_COUNT=0

ok()   { PASS_COUNT=$((PASS_COUNT + 1)); printf "PASS  %s\n" "$1"; }
bad()  { FAIL_COUNT=$((FAIL_COUNT + 1)); printf "FAIL  %s\n" "$1"; }

assert_file_exists() {
  local path="$1"
  if [[ -f "$path" ]]; then
    ok "exists: $path"
  else
    bad "missing: $path"
  fi
}

# assert_file_size <path> <min> <max>  (bytes)
assert_file_size() {
  local path="$1" min="$2" max="$3"
  if [[ ! -f "$path" ]]; then
    bad "size N/A (missing): $path"
    return
  fi
  local size
  size=$(stat -f%z "$path" 2>/dev/null || stat -c%s "$path" 2>/dev/null)
  if [[ "$size" -ge "$min" && "$size" -le "$max" ]]; then
    ok "size $size in [$min, $max]: $path"
  else
    bad "size $size NOT in [$min, $max]: $path"
  fi
}

# assert_contains <path> <fixed-string>
assert_contains() {
  local path="$1" needle="$2"
  if [[ ! -f "$path" ]]; then
    bad "verbatim N/A (missing file): $needle"
    return
  fi
  if grep -F -q -- "$needle" "$path"; then
    ok "contains: $needle"
  else
    bad "missing verbatim: $needle"
  fi
}

# assert_absent <path-glob> <fixed-string>
assert_absent() {
  local glob="$1" needle="$2"
  local hits
  hits=$(grep -rFl -- "$needle" $glob 2>/dev/null || true)
  if [[ -z "$hits" ]]; then
    ok "absent everywhere: $needle"
  else
    bad "found '$needle' in: $hits"
  fi
}

# assert_grep_count <path> <regex> <min> <max>
assert_grep_count() {
  local path="$1" pattern="$2" min="$3" max="$4"
  if [[ ! -f "$path" ]]; then
    bad "regex count N/A (missing): $path"
    return
  fi
  local n
  n=$(grep -E -c -- "$pattern" "$path" || true)
  if [[ "$n" -ge "$min" && "$n" -le "$max" ]]; then
    ok "regex count $n in [$min, $max]: $pattern"
  else
    bad "regex count $n NOT in [$min, $max]: $pattern"
  fi
}

# assert_active_key <html-file> <expected-key>
assert_active_key() {
  local path="$1" key="$2"
  if [[ ! -f "$path" ]]; then
    bad "sidebar active key N/A (missing): $path"
    return
  fi
  if grep -E -q "active=\"$key\"" "$path" || grep -E -q "active=\\{['\"]$key['\"]\\}" "$path"; then
    ok "AdminSidebar active=\"$key\""
  else
    bad "AdminSidebar active key not set to \"$key\""
  fi
}

# Final pass/fail summary; exits 0 if all passed, 1 otherwise.
test_summary() {
  printf "\n──── result ────\n"
  printf "passed: %d  failed: %d\n" "$PASS_COUNT" "$FAIL_COUNT"
  [[ "$FAIL_COUNT" -eq 0 ]]
}
