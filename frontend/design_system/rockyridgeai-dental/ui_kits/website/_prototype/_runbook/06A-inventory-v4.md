# Task 06A — INVENTORY-v4.md

Write the v4 inventory document that every later 06* task reads before doing anything.

## Output

Create exactly one file: `ui_kits/website/_prototype/INVENTORY-v4.md`.

## Allow-list

`^ui_kits/website/_prototype/INVENTORY-v4\.md$`

## What the document must contain

Use markdown headings:

1. **# INVENTORY v4 — Plan v3 (multi-clinic prototype + 4 new config pages)**
2. **## Architecture** — kit (light) vs `_prototype` (dark) split. Kit = PMS, `_prototype` = AI receptionist control plane. Both share `data/clinics.js`, `data/users.js`, `data/ai_config.js`, `lib/auth.js` (already shipped by Plan v2).
3. **## Wordmark** — "Dental AI" everywhere. `_prototype` rebrands every "Receptionist" string. Sidebar group key `'Reception'` stays.
4. **## Two clinics** — `northeast-denture-clinic` (Northeast Denture Clinic) + `market-mall-denture` (Market Mall Denture Clinic). Both already in `data/clinics.js`.
5. **## Owner persona** — Gia Huy / `giahuy.l.hoang@gmail.com` / Owner / `assigned_clinic_ids: ["northeast-denture-clinic", "market-mall-denture"]`. Already in `data/users.js`.
6. **## New pages this round (4)** — `admin-services.html`, `admin-knowledge.html`, `admin-disclosure.html`, `admin-voice.html`. One paragraph each describing what it edits.
7. **## Files touched** — list the full set of files this round modifies (8 admin-*.html, AdminSidebar.jsx, kit Sidebar.jsx, data/admin_mock.js, data/ai_config.js — small additive seed for disclosure+voice).
8. **## DOM hooks** — `rrd-clinic-switcher`, `rrd-clinic-switcher-menu`, `rrd-profile-pill`, `rrd-profile-menu`, `data-clinic-id`, plus active-key strings for new pages: `services`, `knowledge`, `disclosure`, `voice`.
9. **## Kit cross-link** — one new nav item in kit `Sidebar.jsx`: `key: 'ai-receptionist'`, `label: 'AI Receptionist'`, `href: 'login.html?next=_prototype/admin-dashboard.html&relogin=1'`. Click clears session via `RRD.logout()`. Login.html supports `?next=` already.
10. **## Verbatim copy** — the 4 new-page binding strings (one section per page), quoted in fenced code blocks so they cannot be mis-copied.
11. **## dental-api endpoint reference (read-only this round)** — list 6-10 dental-api endpoint paths (e.g. `GET /api/services`, `PATCH /api/clinics/me`, `GET /api/v2/communications/templates`) so a future task can wire them up. Mock-only this round.
12. **## dental-agent surfaces still pending** — list 4-7 dental-agent configurable surfaces NOT shipped this round (triage questions, prompt templates, feature flags, SMS sender, pricing guardrails, LLM/STT/TTS profile selection).
13. **## Out of scope** — wiring to live dental-api, dental-agent auth changes, kit dashboard.html AI KPIs, migrating other data/*.js to clinic-keyed.

## Verbatim required (must appear in the file)

- `Plan v3`
- `_prototype`
- `Dental AI`
- `northeast-denture-clinic`
- `market-mall-denture`
- `admin-services.html`
- `admin-knowledge.html`
- `admin-disclosure.html`
- `admin-voice.html`
- `Kit cross-link`
- `AI Receptionist`
- `dental-api`
- `dental-agent`
- `rrd-clinic-switcher`
- `rrd-profile-pill`
- `Phase 0 v4`

## Success criteria

- File size 5–25 KB.
- All verbatim strings present.
- File begins with `# INVENTORY v4`.
- No emoji.
- Clinical voice (no hype words).

## Constraints

- "We → you" framing.
- Definite article on system names: *The Sidebar. The Profile menu.*
- No emoji.
