# R10 — /settings from settings.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/settings.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/settings/page.tsx` (overwrite)

## Composition
Port the **full 12-tab structure** from the HTML. The HTML has tabs:
1. Clinic info
2. Working hours
3. Operatories
4. Providers
5. Users & roles
6. Integrations  ← LOCKED
7. Notifications  ← LOCKED
8. Audit log
9. AI Greeting
10. AI Routing
11. AI Services
12. AI Knowledge

(Verify the actual list and order from the HTML — that wins over this list.)

## Locked tabs
For tabs 6 (Integrations) and 7 (Notifications), the tab BODY renders `<LockedFeature title="Integrations" body="..." backHref="/settings" />` (and similarly for Notifications). The tab itself stays clickable.

## Data wiring
- Clinic info → `/api/v2/settings/clinic` (existing).
- Working hours → existing endpoint.
- Other tabs (Operatories, Providers, Users & roles, Audit log, AI tabs) — wire to existing endpoints if present, else port HTML seed with TODO.

## Done when
- All 12 tabs render (per HTML order).
- Integrations + Notifications tabs render LockedFeature in body.
- `cd web && npx next build` green.
