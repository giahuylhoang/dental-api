# Task 05E — lib/auth.js extension

Extend the existing session helper with three new functions: `setCurrentClinic(id)`, `getCurrentClinicId()`, `getAssignedClinicIds()`. Also update `RRD.login` to copy `assigned_clinic_ids` from the matched user into the session. All existing functions remain.

## Output

Modify exactly one file: `lib/auth.js`.

## Allow-list

`^lib/auth\.js$`

## Goal

After this task:
- The session JSON includes `assigned_clinic_ids` (array, populated from `users.js` row).
- `RRD.getCurrentClinicId()` returns `getSession()?.clinic_id || null`.
- `RRD.getAssignedClinicIds()` returns `getSession()?.assigned_clinic_ids || []`.
- `RRD.setCurrentClinic(id)` mutates the session's `clinic_id` (only if `id` is in `assigned_clinic_ids`), writes back to localStorage, and dispatches `window.dispatchEvent(new CustomEvent('clinic-changed', { detail: { id } }))`.

## Approach

Read the existing `lib/auth.js` (it is currently 49 lines with `getSession`, `login`, `logout`, `requireSession`). Keep all four existing functions byte-identical except for one minimal change inside `RRD.login`: when building the `session` object, also copy `assigned_clinic_ids: match.assigned_clinic_ids || [match.clinic_id]` (fallback to a single-clinic array for legacy users without the array).

Append three new functions to the IIFE before its closing `})()`:

```js
  RRD.getCurrentClinicId = function () {
    return RRD.getSession()?.clinic_id || null;
  };

  RRD.getAssignedClinicIds = function () {
    return RRD.getSession()?.assigned_clinic_ids || [];
  };

  RRD.setCurrentClinic = function (id) {
    const sess = RRD.getSession();
    if (!sess) return false;
    const allowed = sess.assigned_clinic_ids || [];
    if (allowed.length && !allowed.includes(id)) return false;
    sess.clinic_id = id;
    localStorage.setItem(KEY, JSON.stringify(sess));
    try {
      window.dispatchEvent(new CustomEvent('clinic-changed', { detail: { id } }));
    } catch (_) { /* no-op */ }
    return true;
  };
```

## Verbatim required (these strings must appear in the file)

- `setCurrentClinic`
- `getCurrentClinicId`
- `getAssignedClinicIds`
- `clinic-changed`
- `assigned_clinic_ids`
- `getSession` *(must still be present from the original)*
- `RRD.login` *(must still be present)*
- `RRD.logout` *(must still be present)*
- `requireSession` *(must still be present)*
- `localStorage.setItem(KEY` *(the original storage call pattern, unchanged)*

## Forbidden

- Removing or renaming `getSession`, `login`, `logout`, `requireSession`.
- Changing the `KEY` constant from `'rrd_session'`.
- Importing any module (the file must remain a self-contained IIFE).

## Success criteria

- File size between 1.5 KB and 6 KB.
- All seven function names above appear in the file.
- `assigned_clinic_ids:` (with colon) appears at least twice (once in login, once in getter).
- The IIFE wrapper `(function () {` … `})();` is preserved.
- File parses as JavaScript (no syntax errors).

## Constraints

- Pure additive change to `RRD.login`: the new key is added at the end of the session object (after `issued_at`).
- Do not introduce dependencies on `window.CLINICS` here — `lib/auth.js` should remain a low-level helper that only knows about users and sessions.
- Keep comments matching the existing terse style.
