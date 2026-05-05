# INVENTORY v4 — Plan v3 (multi-clinic prototype + 4 new config pages)

This document is the single source of truth for every 06* task. Read it before writing any code. If a task contradicts this inventory, the inventory wins.

---

## Architecture

The product ships two distinct surfaces that share a common data and auth layer.

**The kit** (`ui_kits/website/*.html`, `Sidebar.jsx`, `TopBar.jsx`, etc.) is the light-theme PMS — the clinical workspace where your front desk manages patients, schedules, labs, and billing. Light theme is the default for every clinical surface; operators look at it for eight-hour shifts.

**The `_prototype`** (`ui_kits/website/_prototype/admin-*.html`, `AdminSidebar.jsx`) is the dark-navy AI receptionist control plane. It is intentionally distinct from the clinical surface: dark `--rr-navy` backgrounds, warm-white text, steel accents. This is where clinic owners configure how the AI agent answers the phone, routes calls, manages services, and discloses its nature to callers.

Both surfaces share:

- `data/clinics.js` — the two-clinic seed (already shipped by Plan v2).
- `data/users.js` — owner and staff records (already shipped by Plan v2).
- `data/ai_config.js` — per-clinic AI configuration, keyed by `clinic_id` (already shipped by Plan v2).
- `lib/auth.js` — session management with `setCurrentClinic`, `getCurrentClinicId`, `getAssignedClinicIds`, and the `clinic-changed` event (already shipped by Plan v2).

The kit does not render AI-configuration UI. The `_prototype` does not render clinical PMS UI. The only bridge is a single nav item in the kit Sidebar that logs the user out and redirects to the `_prototype` login flow.

---

## Wordmark

**Dental AI** is the product brand everywhere in the `_prototype`. Plan v3 rebrands every occurrence of "Receptionist", "RECEPTIONIST", and "The Receptionist" to "Dental AI", "DENTAL AI", or "Dental AI" respectively — in HTML `<title>` tags, breadcrumbs, page headings, and The AdminSidebar wordmark.

The sidebar navigation group key `'Reception'` **stays unchanged**. It is a functional grouping (Dashboard, Calls, Call Detail), not the brand name.

---

## Two clinics

| id | display_name | timezone |
|---|---|---|
| `northeast-denture-clinic` | Northeast Denture Clinic | America/Edmonton |
| `market-mall-denture` | Market Mall Denture Clinic | America/Edmonton |

Both clinics are already seeded in `data/clinics.js`. The owner switches between them via The Sidebar's clinic-switcher pill; the active `clinic_id` propagates to every data query and AI-config read on the page.

---

## Owner persona

| Field | Value |
|---|---|
| Name | Gia Huy |
| Email | giahuy.l.hoang@gmail.com |
| Role | Owner |
| assigned_clinic_ids | `["northeast-denture-clinic", "market-mall-denture"]` |
| Default clinic_id | `northeast-denture-clinic` |

The owner record is already seeded in `data/users.js`. Pages that display the owner's name or email pull from `window.RRD.getSession()`.

---

## New pages this round (4)

Plan v3 adds four configuration pages to the `_prototype`. Each page edits a distinct slice of the AI agent's behaviour for the currently selected clinic.

**`admin-services.html`** — The Service catalogue. Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only. The page reads from `data/services.js` (clinic-keyed) and renders a toggle list. Sidebar active key: `services`.

**`admin-knowledge.html`** — The Knowledge base. Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions. The page renders a document list with upload and delete controls. Sidebar active key: `knowledge`.

**`admin-disclosure.html`** — The AI Disclosure panel. When required by law, the AI must say it's not human at the start of every call. The page provides a toggle and a customisable disclosure statement. Sidebar active key: `disclosure`.

**`admin-voice.html`** — The Voice and Persona panel. What the AI calls itself, what it calls your providers, and what it asks for first. The page configures the agent's display name, provider titles, and intake questions. Sidebar active key: `voice`.

---

## Files touched

The full set of files modified or created by Plan v3 tasks:

### `_prototype` pages (8 existing + 4 new)

| File | Change |
|---|---|
| `admin-dashboard.html` | Rebrand to Dental AI, add clinic switcher + profile pill |
| `admin-calls.html` | Rebrand to Dental AI, add clinic switcher + profile pill |
| `admin-call-detail.html` | Rebrand to Dental AI, add clinic switcher + profile pill |
| `admin-patients.html` | Rebrand to Dental AI, add clinic switcher + profile pill |
| `admin-schedule.html` | Rebrand to Dental AI, add clinic switcher + profile pill |
| `admin-greeting.html` | Rebrand to Dental AI, add clinic switcher + profile pill |
| `admin-routing.html` | Rebrand to Dental AI, add clinic switcher + profile pill |
| `admin-shell.html` | Rebrand to Dental AI, add clinic switcher + profile pill |
| `admin-services.html` | **New** — service catalogue configuration |
| `admin-knowledge.html` | **New** — knowledge base management |
| `admin-disclosure.html` | **New** — AI disclosure toggle and statement |
| `admin-voice.html` | **New** — voice and persona settings |

### Shared components

| File | Change |
|---|---|
| `AdminSidebar.jsx` | Rebrand wordmark to Dental AI, add clinic-switcher pill, add nav entries for the 4 new pages |

### Kit (light-theme PMS)

| File | Change |
|---|---|
| `ui_kits/website/Sidebar.jsx` | Add one nav item: AI Receptionist with `NEW` badge |

### Data and config

| File | Change |
|---|---|
| `data/admin_mock.js` | Populate with operational data (calls, patients, appointments) keyed by clinic id |
| `data/ai_config.js` | Small additive seed for disclosure and voice configuration per clinic |

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

### The Topbar — profile popover

| Attribute | Element | Purpose |
|---|---|---|
| `id="rrd-profile-pill"` | Pill button | Toggles the profile popover. |
| `id="rrd-profile-menu"` | Popover container | Contains Account and Sign out items. `role="menu"`. |

Sign out calls `RRD.logout()` then navigates to `login.html?logout=1`.

### New page active keys

| Page | Sidebar active key |
|---|---|
| `admin-services.html` | `services` |
| `admin-knowledge.html` | `knowledge` |
| `admin-disclosure.html` | `disclosure` |
| `admin-voice.html` | `voice` |

---

## Kit cross-link

The kit `Sidebar.jsx` gains one new nav item:

| Property | Value |
|---|---|
| key | `ai-receptionist` |
| label | `AI Receptionist` |
| badge | `NEW` |
| href | `login.html?next=_prototype/admin-dashboard.html&relogin=1` |

Clicking the item clears the current session via `RRD.logout()`, then navigates to the href. The login page already supports the `?next=` parameter and will redirect to the `_prototype` dashboard after successful authentication.

This is the only bridge between the kit and the `_prototype`. The two surfaces do not share navigation chrome.

---

## Verbatim copy

The strings below must appear in the rendered DOM exactly as written. Fenced code blocks preserve the exact characters.

### admin-services.html

```
Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only.
```

### admin-knowledge.html

```
Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions.
```

### admin-disclosure.html

```
When required by law, the AI must say it's not human at the start of every call.
```

### admin-voice.html

```
What the AI calls itself, what it calls your providers, and what it asks for first.
```

### Carried forward from prior phases

```
AI SIP URI (read-only here; engineer-managed)
```

```
Both blank means closed that day.
```

```
Welcome to … How can I help you today?
```

(The `…` above is U+2026, a single ellipsis character.)

---

## dental-api endpoint reference (read-only this round)

The following endpoints represent the dental-api contract that the `_prototype` pages will wire up in a future round. This round uses mock data only; no network calls are made.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/services` | List all services for the current clinic |
| `PATCH` | `/api/services/:id` | Update a service's AI-bookable flag |
| `GET` | `/api/knowledge` | List knowledge-base documents for the current clinic |
| `POST` | `/api/knowledge` | Upload a new knowledge-base document |
| `DELETE` | `/api/knowledge/:id` | Remove a knowledge-base document |
| `GET` | `/api/clinics/me` | Fetch the current clinic's configuration |
| `PATCH` | `/api/clinics/me` | Update clinic-level settings (disclosure, voice, persona) |
| `GET` | `/api/v2/communications/templates` | List communication templates (greeting, disclosure statement) |
| `PUT` | `/api/v2/communications/templates/:id` | Update a communication template |

---

## dental-agent surfaces still pending

The following configurable surfaces are not shipped this round. They remain on the roadmap for future Plan iterations.

1. **Triage questions** — configurable intake questions the agent asks before routing a call (beyond the default name + reason).
2. **Prompt templates** — editable system prompts and few-shot examples that shape the agent's conversational behaviour.
3. **Feature flags** — per-clinic toggles for experimental agent capabilities (voicemail transcription, SMS follow-up, hold music selection).
4. **SMS sender configuration** — outbound SMS number assignment, opt-in/opt-out management, message templates.
5. **Pricing guardrails** — maximum quote amounts the agent is allowed to communicate before deferring to the front desk.
6. **LLM / STT / TTS profile selection** — choice of language model, speech-to-text engine, and text-to-speech voice per clinic.
7. **Call transfer rules** — configurable escalation paths (direct transfer to provider, warm handoff to front desk, voicemail fallback).

---

## Out of scope

The following items are explicitly excluded from the 06* task series:

- Wiring `_prototype` pages to the live dental-api. All data is mock-only this round.
- dental-agent authentication changes. The agent's own auth flow (SIP registration, SRTP credentials) is managed outside the kit.
- Kit `dashboard.html` AI KPIs. The kit dashboard does not display AI-related metrics this round.
- Migrating other `data/*.js` files to the clinic-keyed scheme. Only `ai_config.js` and `admin_mock.js` are in scope.
- User-facing theme toggle. The kit is light-theme only; the `_prototype` is dark-theme only. Neither surface offers a toggle.

---

## Phase 0 v4

This file is Phase 0. It documents the locked decisions, binding contracts, and verbatim copy that every subsequent 06* phase depends on.

Later phases produce the actual artefacts:

- **Phase 1** — `data/admin_mock.js` operational data seed (calls, patients, appointments keyed by clinic id).
- **Phase 2** — `data/ai_config.js` additive seed (disclosure and voice configuration per clinic).
- **Phase 3** — `AdminSidebar.jsx` rebrand + clinic switcher + new nav entries.
- **Phase 4** — Rebrand all 8 existing `admin-*.html` pages to Dental AI with clinic switcher and profile pill.
- **Phase 5** — `admin-services.html` — The Service catalogue page.
- **Phase 6** — `admin-knowledge.html` — The Knowledge base page.
- **Phase 7** — `admin-disclosure.html` — The AI Disclosure page.
- **Phase 8** — `admin-voice.html` — The Voice and Persona page.
- **Phase 9** — Kit `Sidebar.jsx` — AI Receptionist cross-link.
- **Phase 10** — End-to-end verification against the test suite.

Each phase reads this inventory before writing any code. If a phase discovers a conflict with this document, the inventory is updated first, then the code follows.
