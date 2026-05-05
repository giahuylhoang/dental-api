# Task 06L — Plan v3 integrity verification

The authoritative test lives at `_runbook/_tests/06L.test.sh`. Run from `rockyridgeai-dental.com/`:

    bash ui_kits/website/_prototype/_runbook/_tests/06L.test.sh

## Assertions

1. Branding sweep: every `_prototype/admin-*.html` `<title>` contains `Dental AI` and `Receptionist` is absent across all 8 admin-*.html and AdminSidebar.jsx.
2. AdminSidebar.jsx renders the clinic switcher (`id="rrd-clinic-switcher"`).
3. Each `_prototype/admin-*.html` topbar renders `id="rrd-profile-pill"` exactly once.
4. `data/admin_mock.js` has `setCurrentClinic` + `CLINICS["northeast-denture-clinic"]` + `CLINICS["market-mall-denture"]`.
5. Four new pages exist: `admin-services.html`, `admin-knowledge.html`, `admin-disclosure.html`, `admin-voice.html`. Each contains its required verbatim copy.
6. `AdminSidebar.jsx` config group lists all 6 children: Routing, Greeting, Services, Knowledge, AI disclosure, Voice & persona.
7. Kit `Sidebar.jsx` has `key: 'ai-receptionist'` with href to `login.html?next=_prototype/admin-dashboard.html&relogin=1` and a `NEW` badge.
8. Kit `Sidebar.jsx` still has all 10 original nav keys (regression guard): dashboard, patients, schedule, plans, lab, billing, comms, crm, reports, settings.
9. `data/ai_config.js` has `disclosure` and `voice` blocks for both clinics.

## How to interpret failures

Each assertion writes a single PASS or FAIL line. Re-run the test after a file edit to see whether the issue is resolved without re-dispatching kiro-cli.
