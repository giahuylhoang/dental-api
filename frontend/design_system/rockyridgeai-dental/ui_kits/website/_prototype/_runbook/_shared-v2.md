# Shared context for every 05* task (Multi-Clinic Owner Workspace, Plan v2)

**Read this once. Treat it as binding.** It supersedes `_shared.md` (which was written for the legacy dark `_prototype/admin-*.html` flow).

## What we're building

The Rockyridge Dental AI design kit at `rockyridgeai-dental.com/` is the brand-correct, light-theme PMS. We are extending it — not replacing it — to support a single business owner managing multiple dental clinics, with AI-receptionist configuration native to the kit's existing `settings.html`.

The dark `_prototype/admin-*.html` pages exist but are legacy. They are out of scope for every 05* task. Do not edit them. Do not reference them as a pattern.

## Ground truth (read these first, in this order)

1. `rockyridgeai-dental.com/SKILL.md` — design lineage and brand rules. Light theme is default; dark only on `login.html`. No emoji. Lucide icons stroke 1.5. Brand voice: clinical, calm, authoritative; "we → you"; definite article on system names ("The Schedule", "The Roster").
2. `rockyridgeai-dental.com/README.md` — token contract. Every colour/spacing/font value must come from `colors_and_type.css`.
3. `rockyridgeai-dental.com/ui_kits/website/_prototype/INVENTORY-v3.md` — locked decisions for v2 (clinic ids, owner persona, tab list, hooks). If a task contradicts this inventory, the inventory wins.
4. `rockyridgeai-dental.com/ui_kits/website/settings.html` — canonical pattern for settings tabs; mirror the `tab-bar` / `tab-btn` / `panel` / `field` / `field-row` / `lbl` / `d-input` / `pill` / `toggle-row` / `int-card` classnames already defined in its `<style>` block.
5. `rockyridgeai-dental.com/ui_kits/website/Sidebar.jsx` and `TopBar.jsx` — chrome contracts. Existing exports via `Object.assign(window, { Sidebar })` / `Object.assign(window, { TopBar })` must be preserved.
6. `rockyridgeai-dental.com/lib/auth.js` — session model. `RRD.getSession()`, `RRD.login(email, password)`, `RRD.logout()`, `RRD.requireSession(loginPath?)`. Session JSON has: `clinic_id`, `user_id`, `full_name`, `email`, `role`, `issued_at`. Plan v2 adds: `assigned_clinic_ids`.

## Brand voice (binding)

- Clinical, calm, authoritative.
- "We → you" framing. *We* (Rockyridge) build; *you* (the clinic) run.
- No hype: never "AI-powered", "world-class", "cutting-edge", "seamless", "delight", "smart". Concrete specifics only.
- Definite article on system names: *The Schedule. The Roster. The Lab. The Greeting. The Routing.* Capitalised, proper nouns. Nav labels stay bare ("Settings", "Patients").
- No emoji. Anywhere.
- Casing: ALL CAPS overlines with 0.15em tracking. Title Case for CTAs ("Save greeting", "Save routing"). Sentence case for descriptive copy.

## Kit mechanics (binding)

- Pages live at `ui_kits/website/*.html`. Self-contained — no bundler. React + ReactDOM + Babel via UMD CDN.
- Stylesheet: `<link rel="stylesheet" href="../../colors_and_type.css">` for kit pages (settings.html depth). Tokens: `var(--rr-navy)`, `var(--rr-warm-white)`, `var(--rr-parchment)`, `var(--rr-mist)`, `var(--rr-ink)`, `var(--rr-slate-dark)`, `var(--rr-steel-700)`, `var(--font-display|ui|mono)`, `hsl(var(--primary))`, `hsl(var(--ring))`. Do not redefine.
- Mock data: every page should `<script src="../../data/<file>.js">` for whichever seeds it consumes. The seed manifest lives at `data/index.js`.
- Helpers: `<script src="../../lib/auth.js">` and `<script src="../../lib/query.js">` come before the JSX. Top of `<script type="text/babel">`: `window.RRD.requireSession?.();`.
- Hooks: `React.useState`, `React.useEffect`, `React.useRef`. UMD does not expose destructured hooks; always namespace through `React.`.
- Mount: `ReactDOM.createRoot(document.getElementById('root')).render(<App />);`.

## Owner persona (binding)

- Name: `Gia Huy`
- Email: `giahuy.l.hoang@gmail.com`
- Role: `Owner`
- Assigned clinics: `["northeast-denture-clinic", "market-mall-denture"]`
- Default `clinic_id` after login: `northeast-denture-clinic`

## Two clinics (binding)

| id | display_name | timezone | contact_phone |
|---|---|---|---|
| `northeast-denture-clinic` | Northeast Denture Clinic | America/Edmonton | +15879738089 |
| `market-mall-denture` | Market Mall Denture Clinic | America/Edmonton | +13682990959 |

## DOM hooks (binding)

- Clinic switcher (in `Sidebar.jsx`): `id="rrd-clinic-switcher"`, dropdown `id="rrd-clinic-switcher-menu"`. Each menu item carries `data-clinic-id="<id>"` and `role="menuitem"`. Pill must use `aria-expanded`.
- Profile pill (in `TopBar.jsx`): `id="rrd-profile-pill"`. Popover: `id="rrd-profile-menu"`, `role="menu"`. Menu items: `Account`, `Sign out`. Sign out calls `RRD.logout()` then navigates to `login.html?logout=1`.
- New tab buttons in `settings.html`: text content exactly `AI Greeting`, `AI Routing`, `AI Services`, `AI Knowledge`. Existing 8 tabs (`Clinic info`, `Working hours`, `Operatories`, `Providers`, `Users & roles`, `Integrations`, `Notifications`, `Audit log`) must remain present and unmodified.

## Verbatim copy contract (binding)

When the task says "verbatim", the string must appear in the rendered DOM **exactly** as written, including punctuation, the U+2026 ellipsis, and case. Common strings owed:

- `Welcome to … How can I help you today?` (textarea placeholder; `…` is U+2026)
- `0 / 280 characters`
- `No custom greeting persisted yet. The agent uses the YAML default until you save one.`
- `First-time edits land as pending_review. An engineer (email allow-listed in GREETING_APPROVERS) must call /approve once per clinic; after that, edits auto-approve.`
- `Approve clinic (engineer-gated)`
- `AI SIP URI (read-only here; engineer-managed)`
- `Both blank means closed that day.`
- `What would the agent do at a given moment, against the currently saved rules? (Save first if you want to preview a draft.)`
- `Sign in to your workspace`

## Forbidden files (never edit unless the task explicitly allow-lists)

- `colors_and_type.css`
- `SKILL.md`, `README.md`
- `_prototype/admin-*.html` (legacy)
- `_prototype/_runbook/_tests/_lib.sh`
- `_prototype/_runbook/_shared.md` (the old shared file; we use `_shared-v2.md` now)
- Any existing tab body inside `settings.html` (`tab === 0` … `tab === 7`) — they must remain byte-identical
- Any `data/*.js` not on the per-task allow-list

## Smoke test contract

After writing files, run the task's external test from `rockyridgeai-dental.com/`:

```
bash ui_kits/website/_prototype/_runbook/_tests/<id>.test.sh
```

The test is **authoritative**. The runbook driver runs it after kiro-cli finishes; if it fails, the driver re-prompts with the test output. Do not declare done if the test fails — instead, edit the file to satisfy the failing line.

## Output contract

Write only the file(s) the task names. Do not modify any other file. Do not start an HTTP server. After success, the runbook driver writes `_runbook/_state/<id>.done.md` automatically — you do not need to write this yourself.
