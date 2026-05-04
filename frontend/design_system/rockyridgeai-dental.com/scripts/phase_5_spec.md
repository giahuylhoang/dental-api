# Phase 5 — Simulated auth flow

## Goal

Make the site behave like a real authenticated app:
1. Visiting any app page without a session redirects to `login.html?next=<this-page>`.
2. Submitting login (any email + password ≥ 6 chars) sets `localStorage.rrd_session` and lands on `dashboard.html` (or whatever `?next=` was).
3. Logout clears the session and returns to `login.html`.
4. `TopBar` user pill shows the current user's `full_name` from the session.

## Working directory

`frontend/design_system/rockyridgeai-dental.com/`

## Files to edit

### 1. `lib/auth.js` (already partially scaffolded — verify and extend)

Must export, on `window.RRD`:
- `getSession()` → object or null
- `login(email, password)` → `{ ok: true, session }` or `{ ok: false, error }`
- `logout()` → void; clears `localStorage.rrd_session`
- `requireSession(loginPath = 'login.html')` → object (returns the session) or redirects

Behavior:
- `login(email, password)` looks up `window.USERS` (loaded from `data/users.js`); if a user has matching email it's used; otherwise the first user is used (demo fallback). The password is only validated for length (≥ 6 chars), not the actual value.
- `requireSession()` — if no session, redirect via `window.location.replace` to `loginPath?next=<encodeURIComponent(currentPath)>`.

### 2. `ui_kits/website/login.html`
- The "Sign in" button submits a form. Replace any current handler with one that:
  1. Reads `email` and `password` from the form.
  2. Calls `window.RRD.login(email, password)`.
  3. On success, reads `?next=` from the URL; if present, `window.location.assign(decodeURIComponent(next))`. Else `window.location.assign('dashboard.html')`.
  4. On failure, renders the error message under the form.
- `<script src="../../data/users.js"></script>` must be loaded before the form-handler script.
- `<script src="../../lib/auth.js"></script>` must be loaded too.
- If `?logout=1` is in the URL, call `RRD.logout()` on page load (so the existing TopBar logout link `login.html?logout=1` does the right thing).

### 3. Every app page (NOT `login.html` and NOT `index.html`)

At the top of the `<script type="text/babel">` block:
```js
window.RRD?.requireSession?.();
```

(This is a no-op if `auth.js` hasn't loaded yet — but the test will check that the call exists in source.)

Make sure `<script src="../../lib/auth.js"></script>` is loaded BEFORE the babel block on these pages (and `data/users.js` is loaded before `auth.js` so the global is available when `login()` runs).

### 4. `ui_kits/website/TopBar.jsx`
- The user pill on the right reads `window.RRD?.getSession?.()?.full_name || 'Demo Clinician'`.
- The user-menu dropdown shows the email below the name.
- The "Sign out" link (added in Phase 1 with `href="login.html?logout=1"`) stays — the logout actually fires on `login.html` load via `?logout=1`.

## Pass criterion

Run `bash scripts/test_phase5.sh`. It checks:
1. `lib/auth.js` defines `login`, `logout`, `getSession`, `requireSession`.
2. `login.html` calls `RRD.login(...)` and references `dashboard.html`.
3. Every app page calls `requireSession()`.
4. `TopBar.jsx` references `logout` (so the Sign-out link is wired).

## Rules

- `localStorage.rrd_session` is the ONLY auth state; no cookies, no backend.
- Don't change visual styling. Auth is wiring only.
- Don't gate `index.html` (marketing) or `login.html`.
