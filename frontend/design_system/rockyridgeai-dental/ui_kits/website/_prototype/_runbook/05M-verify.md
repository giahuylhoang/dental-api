# Task 05M — Integrity verification

The authoritative test lives at `_runbook/_tests/05M.test.sh`. Run from `rockyridgeai-dental.com/`:

    bash ui_kits/website/_prototype/_runbook/_tests/05M.test.sh

## Assertions

1. `data/clinics.js` exposes both `northeast-denture-clinic` and `market-mall-denture` with non-empty `display_name`.
2. `data/users.js` first row is the Owner (`Gia Huy`, `giahuy.l.hoang@gmail.com`) with `assigned_clinic_ids` covering both clinics.
3. `data/ai_config.js` has a routing + greeting + knowledge_docs block per clinic.
4. `lib/auth.js` exposes `setCurrentClinic`, `getCurrentClinicId`, `getAssignedClinicIds`, and dispatches `clinic-changed`.
5. `Sidebar.jsx` renders `id="rrd-clinic-switcher"` and references `setCurrentClinic` and `data-clinic-id`.
6. `TopBar.jsx` renders `id="rrd-profile-pill"` and `id="rrd-profile-menu"` with `Sign out` link.
7. `settings.html` `TABS` array contains all 12 tab names — 8 original (Clinic info, Working hours, Operatories, Providers, Users & roles, Integrations, Notifications, Audit log) and 4 new (AI Greeting, AI Routing, AI Services, AI Knowledge).
8. Verbatim copy in settings.html: every binding string from `_shared-v2.md` "Verbatim copy contract" appears.
9. `login.html` reads `Sign in to your workspace` and the old `Sign in to your clinic` is absent.

## How to interpret failures

Each assertion writes a single PASS or FAIL line. Re-running the test after a file edit shows whether the issue is resolved without re-dispatching kiro-cli.
