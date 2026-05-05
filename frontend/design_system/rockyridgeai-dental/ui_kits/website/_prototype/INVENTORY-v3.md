# INVENTORY v3 — Multi-Clinic Owner Workspace

This document is the single source of truth for the multi-clinic owner refactor. Every 05* task reads it before doing anything. If a task contradicts this inventory, the inventory wins.

---

## Pivot to the kit

The legacy `_prototype/admin-*.html` pages use a dark theme. SKILL.md is explicit: light theme is the default for every clinical and admin surface. Dark theme is reserved for The Login portal and marketing heroes only. Building an owner workspace on a dark scaffold contradicts the brand contract and forces every downstream component to fight the token system.

Plan v2 corrects this. We build on the kit's existing light-theme chrome — `Sidebar.jsx`, `TopBar.jsx`, `settings.html` — and extend it additively. The Sidebar gains a clinic-switcher pill. The TopBar gains a profile dropdown popover. The Settings panel gains four new AI-configuration tabs. No new page shells are created; no dark admin pages are touched.

The legacy `_prototype/admin-*.html` files remain in the repository for reference but are out of scope for every 05* task.

---

## Two clinics

| id | display_name | timezone | contact_phone |
|---|---|---|---|
| `northeast-denture-clinic` | Northeast Denture Clinic | America/Edmonton | +15879738089 |
| `market-mall-denture` | Market Mall Denture Clinic | America/Edmonton | +13682990959 |

Both clinics operate in the same timezone. The owner switches between them via The Sidebar's clinic-switcher pill; the active `clinic_id` propagates to every data query and AI-config read/write on the page.

---

## Owner persona

| Field | Value |
|---|---|
| Name | Gia Huy |
| Email | giahuy.l.hoang@gmail.com |
| Role | Owner |
| assigned_clinic_ids | `["northeast-denture-clinic", "market-mall-denture"]` |
| Default clinic_id | `northeast-denture-clinic` |

The Owner role grants read/write access to every tab in The Settings panel, including the four AI tabs. Staff users see a reduced tab set (defined per-role in `lib/auth.js`).

---

## Files touched (additive)

Every change is additive. Existing behaviour is preserved; new code layers on top.

- **`data/clinics.js`** (rewrite) — seed file for the two clinics listed above. Replaces the single-clinic stub.
- **`data/users.js`** (rewrite) — owner record for Gia Huy plus two staff records (one per clinic). Replaces the single-user stub.
- **`data/ai_config.js`** (new) — per-clinic AI configuration: greeting text, routing rules, service catalogue, knowledge-base entries. Keyed by `clinic_id`.
- **`lib/auth.js`** (additive) — new helpers on the `RRD` namespace:
  - `RRD.setCurrentClinic(clinicId)` — writes `clinic_id` to the session and fires a `clinic-changed` event on `window`.
  - `RRD.getCurrentClinicId()` — returns the active `clinic_id` from the session.
  - `RRD.getAssignedClinicIds()` — returns the `assigned_clinic_ids` array from the session.
  - `clinic-changed` CustomEvent — any component that reads clinic-scoped data listens for this and re-fetches.
- **`ui_kits/website/Sidebar.jsx`** (additive) — clinic-switcher pill below the logo. DOM hooks: `id="rrd-clinic-switcher"`, dropdown `id="rrd-clinic-switcher-menu"`, each item carries `data-clinic-id` and `role="menuitem"`.
- **`ui_kits/website/TopBar.jsx`** (additive) — profile dropdown popover. DOM hooks: `id="rrd-profile-pill"`, popover `id="rrd-profile-menu"` with `role="menu"`. Menu items: Account, Sign out. Sign out calls `RRD.logout()` then navigates to `login.html?logout=1`.
- **`ui_kits/website/settings.html`** (additive) — four new tab buttons appended to the tab bar: AI Greeting, AI Routing, AI Services, AI Knowledge. Each tab renders a clinic-scoped configuration panel. The existing eight tabs remain byte-identical.
- **`ui_kits/website/login.html`** (one copy change) — heading changes from "Sign in to your clinic" to "Sign in to your workspace".

---

## DOM hooks

Every `id` and `data-` attribute listed here is a binding contract. Tests assert against them.

### The Sidebar — clinic switcher

| Attribute | Element | Purpose |
|---|---|---|
| `id="rrd-clinic-switcher"` | Pill button | Toggles the clinic dropdown. Uses `aria-expanded`. |
| `id="rrd-clinic-switcher-menu"` | Dropdown list | Contains one item per assigned clinic. |
| `data-clinic-id="<id>"` | Each menu item | Identifies the clinic. Value is the clinic `id` from the table above. |
| `role="menuitem"` | Each menu item | Accessibility role for the dropdown items. |

### The TopBar — profile popover

| Attribute | Element | Purpose |
|---|---|---|
| `id="rrd-profile-pill"` | Pill button | Toggles the profile popover. |
| `id="rrd-profile-menu"` | Popover container | Contains Account and Sign out items. `role="menu"`. |

### The Settings panel — AI tabs

The four new tab buttons appear after the existing eight tabs in the tab bar. Their text content is exactly:

- `AI Greeting`
- `AI Routing`
- `AI Services`
- `AI Knowledge`

---

## AI tab verbatim copy

Every string below must appear in the rendered DOM exactly as written. The U+2026 character (`...`) is a single ellipsis, not three periods.

### AI Greeting tab

```
Welcome to ... How can I help you today?
```

(Textarea placeholder. The `...` above is U+2026.)

```
0 / 280 characters
```

```
No custom greeting persisted yet. The agent uses the YAML default until you save one.
```

```
First-time edits land as pending_review. An engineer (email allow-listed in GREETING_APPROVERS) must call /approve once per clinic; after that, edits auto-approve.
```

```
Approve clinic (engineer-gated)
```

### AI Routing tab

```
AI SIP URI (read-only here; engineer-managed)
```

```
Both blank means closed that day.
```

### AI Services tab

No additional verbatim strings beyond the tab label.

### AI Knowledge tab

```
What would the agent do at a given moment, against the currently saved rules? (Save first if you want to preview a draft.)
```

---

## Out of scope

The following items are explicitly excluded from the 05* task series:

- Legacy `_prototype/admin-*.html` pages. They exist for reference only. Do not edit, do not reference as a pattern.
- Dental-agent authentication changes. The agent's own auth flow (SIP registration, SRTP credentials) is managed outside the kit.
- Migrating other `data/*.js` files to the new clinic id scheme. Only `clinics.js`, `users.js`, and `ai_config.js` are in scope.
- User-facing theme toggle. The kit is light-theme only; dark is reserved for The Login portal.

---

## Phase 0 v3

This file is Phase 0. It documents the locked decisions, binding contracts, and verbatim copy that every subsequent phase depends on.

Later phases produce the actual artefacts:

- **Phase 1** — `data/clinics.js`, `data/users.js`, `data/ai_config.js` seed files.
- **Phase 2** — `lib/auth.js` additive helpers (setCurrentClinic, getCurrentClinicId, getAssignedClinicIds, clinic-changed event).
- **Phase 3** — `Sidebar.jsx` clinic-switcher pill, `TopBar.jsx` profile popover.
- **Phase 4** — `settings.html` four AI tabs (AI Greeting, AI Routing, AI Services, AI Knowledge).
- **Phase 5** — `login.html` copy update: "Sign in to your workspace".
- **Phase 6** — End-to-end verification against the test suite.

Each phase reads this inventory before writing any code. If a phase discovers a conflict with this document, the inventory is updated first, then the code follows.
