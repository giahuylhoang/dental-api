# R11 — /login from login.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/login.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(portal)/login/page.tsx` (overwrite)
And update `web/components/dental/LoginCard.tsx` to match HTML's LoginCard.jsx exactly.

## Composition
- Two-column layout (1.05fr / 1fr per HTML grid template).
- Left column: brand panel (Hero / wordmark / tagline / pillars).
- Right column: LoginCard with form fields, sweep-fill submit button.
- Dark theme (already scoped by `(portal)` layout).

## Behavior preservation
- Form submits via existing `login()` from `@/lib/auth/auth`.
- Form **must** keep `method="post"` and `e.preventDefault()` so credentials never leak into URL.
- `autoComplete` tokens stay (`username` on email, `current-password` on password).
- On success, `router.push("/dashboard")`.

## Done when
- Two-column dark login matches HTML.
- Existing login round-trip still works (POST /api/v2/auth/login → 200 → /dashboard).
- `cd web && npx next build` green.
