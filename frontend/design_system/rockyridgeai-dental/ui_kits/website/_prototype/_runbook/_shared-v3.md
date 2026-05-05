# Shared context for every 06* task (Plan v3 — _prototype dark admin)

**Read this once. Treat it as binding.** Plan v3 supersedes `_shared.md` and `_shared-v2.md` for 06* tasks.

## What we're building

The dark-navy `_prototype/admin-*.html` admin is the **AI receptionist control plane** — separate surface from the light kit (which is the PMS). Plan v3 brings the multi-clinic owner experience (already shipped on the kit by Plan v2) to the prototype: clinic switcher in the sidebar, owner profile dropdown in the topbar, four new configuration pages (Services, Knowledge, AI Disclosure, Voice & Persona), and a unified "Dental AI" wordmark.

The prototype currently brands itself "Rockyridge Receptionist". Plan v3 rebrands every "Receptionist" / "RECEPTIONIST" / "The Receptionist" string to "Dental AI" / "DENTAL AI" / "Dental AI" so the brand matches the kit and `login.html`.

The kit gets one new sidebar entry: `AI Receptionist` with a `NEW` badge. Clicking it logs the user out and forces re-login, then lands them in the prototype dashboard. This is the **only** kit file that changes (`ui_kits/website/Sidebar.jsx`).

## Ground truth (read these first)

1. `rockyridgeai-dental.com/SKILL.md` — design lineage. Light theme is default; **the dark `_prototype/` is an exception** — it's the operator-facing AI control plane, intentionally distinct from clinical surfaces. No emoji. Clinical, calm voice.
2. `rockyridgeai-dental.com/README.md` — token contract.
3. `rockyridgeai-dental.com/ui_kits/website/_prototype/INVENTORY-v4.md` — Plan v3 ground truth (locked decisions, file list, verbatim copy). Created by 06A; once present, it wins over this file.
4. `rockyridgeai-dental.com/ui_kits/website/_prototype/admin-routing.html` — the canonical reference for prototype panel structure, switch / hours-row primitives, sticky save bar, navy `--rr-navy` save buttons. Mirror its conventions.
5. `rockyridgeai-dental.com/ui_kits/website/_prototype/AdminSidebar.jsx` — the sidebar component. Must mount on every admin-*.html via `<AdminSidebar active="<key>" clinicName={...} clinicSlug={...} />`.
6. `rockyridgeai-dental.com/data/ai_config.js` — per-clinic AI config (already keyed by clinic_id from Plan v2). Pages read `window.AI_CONFIG[currentClinicId]`.
7. `rockyridgeai-dental.com/data/clinics.js`, `data/users.js` — already in their final v2 state. Re-use; never edit.
8. `rockyridgeai-dental.com/lib/auth.js` — already extended in v2 with `setCurrentClinic`, `getCurrentClinicId`, `getAssignedClinicIds`, `clinic-changed` event.

## Brand voice (binding)

- Clinical, calm, authoritative.
- "We → you" framing.
- No hype: never "AI-powered", "world-class", "cutting-edge", "seamless", "delight", "smart".
- Definite article on system names: *The Routing. The Greeting. The Knowledge base. The Service catalogue.*
- No emoji. Anywhere.
- Casing: ALL CAPS overlines, Title Case CTAs, sentence case body.

## Wordmark (binding)

**"Dental AI"** everywhere. Replaces "Receptionist" in every prototype HTML title, breadcrumb, page heading, and the AdminSidebar wordmark. The sidebar group label `'Reception'` (which groups Dashboard + Calls + Call Detail nav items) **stays** — it's a functional nav grouping, not the brand.

## Kit mechanics (binding)

- Pages live at `ui_kits/website/_prototype/*.html`. Self-contained — no bundler. React + ReactDOM + Babel via UMD CDN.
- Stylesheet: `<link rel="stylesheet" href="../../../colors_and_type.css">` (the prototype is at depth `../../../`, NOT `../../`).
- Tokens: `var(--rr-navy)`, `var(--rr-warm-white)`, `var(--rr-parchment)`, `var(--rr-mist)`, `var(--rr-ink)`, `var(--rr-slate-dark)`, `var(--rr-steel-700)`, `var(--font-display|ui|mono)`, `hsl(var(--primary))`, `hsl(var(--ring))`. Do not redefine.
- Mock data scripts: `<script src="../../../data/clinics.js">`, `<script src="../../../data/admin_mock.js">`, `<script src="../../../data/ai_config.js">`, `<script src="../../../data/services.js">`.
- Helpers: `<script src="../../../lib/query.js">`, `<script src="../../../lib/auth.js">`, `<script src="../../../lib/console-tap.js">` (the dev tap).
- Top of `<script type="text/babel">`: `window.RRD?.requireSession?.();`
- Sidebar: `<script type="text/babel" src="AdminSidebar.jsx"></script>`
- Mount root: `<div id="root"></div>` then `ReactDOM.createRoot(document.getElementById('root')).render(<Body />);`
- Hooks: always `React.useState`, `React.useEffect`, `React.useRef` (UMD doesn't expose hooks bare).

## Owner persona (binding, from v2)

- Name: `Gia Huy`
- Email: `giahuy.l.hoang@gmail.com`
- Role: `Owner`
- Assigned clinics: `["northeast-denture-clinic", "market-mall-denture"]`

Pages that show the owner pull from `window.RRD.getSession()` (set by `lib/auth.js` after login).

## Two clinics (binding)

| id | display_name | timezone |
|---|---|---|
| `northeast-denture-clinic` | Northeast Denture Clinic | America/Edmonton |
| `market-mall-denture` | Market Mall Denture Clinic | America/Edmonton |

Already in `data/clinics.js`. Plan v3 06C populates `data/admin_mock.js` with operational data (calls / patients / appointments) keyed by these ids.

## DOM hooks (binding)

- Clinic switcher (in `_prototype/AdminSidebar.jsx`): `id="rrd-clinic-switcher"`, dropdown `id="rrd-clinic-switcher-menu"`. Each menu item: `data-clinic-id="<id>"`, `role="menuitem"`. Pill: `aria-expanded`.
- Profile pill (in each `admin-*.html` topbar): `id="rrd-profile-pill"`. Popover: `id="rrd-profile-menu"`, `role="menu"`. Items: `Account`, `Sign out`. Sign out calls `RRD.logout()` then navigates to `login.html?logout=1`.
- New nav keys (added in 06K): `services`, `knowledge`, `disclosure`, `voice`. Pages set `<AdminSidebar active="<key>" />`.

## Verbatim copy contract (binding)

When a task says "verbatim", the string must appear in the rendered DOM **exactly** as written. Common strings:

- `Welcome to … How can I help you today?` (`…` is U+2026)
- `Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only.`
- `Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions.`
- `When required by law, the AI must say it's not human at the start of every call.`
- `What the AI calls itself, what it calls your providers, and what it asks for first.`
- `AI SIP URI (read-only here; engineer-managed)` (already present in `admin-routing.html` from prior phases)
- `Both blank means closed that day.` (already present)

## Forbidden files (never edit unless the task explicitly allow-lists)

- `colors_and_type.css`, `SKILL.md`, `README.md`
- The kit (`ui_kits/website/*.html` outside `_prototype/`) — except `Sidebar.jsx` (06J only)
- `data/clinics.js`, `data/users.js`, `lib/auth.js`, `lib/query.js`, `lib/console-tap.js`
- `_prototype/_runbook/_tests/_lib.sh`
- `_prototype/_runbook/_shared.md` (legacy v1) and `_shared-v2.md` (v2)
- Any `_state/*.done.md` from prior tasks
- Any `data/*.js` not on the per-task allow-list

## Smoke test contract

After writing files, run the task's external test:

```
bash ui_kits/website/_prototype/_runbook/_tests/<id>.test.sh
```

The test is **authoritative**. The runbook driver runs it after kiro-cli finishes; if it fails, the driver re-prompts with the test output. Do not declare done if the test fails — edit in place to satisfy each FAIL.

## Output contract

Write only the file(s) the task names. Do not modify any other file. Do not start any HTTP server. The runbook driver writes `_state/<id>.done.md` automatically on success.
