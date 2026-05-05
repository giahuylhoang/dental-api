# Task 05A — INVENTORY-v3.md

Write the v3 inventory document that every later 05* task reads before doing anything. This is the single source of truth for the multi-clinic owner refactor.

## Output

Create exactly one file: `ui_kits/website/_prototype/INVENTORY-v3.md`.

## Allow-list

`^ui_kits/website/_prototype/INVENTORY-v3\.md$`

## Goal

A clinic owner runs through the kit and immediately sees the multi-clinic owner experience. This file documents what we agreed, what we touched, and how to verify.

## What the document must contain

Use this top-level structure (markdown headings):

1. **# INVENTORY v3 — Multi-Clinic Owner Workspace** (top heading; verbatim)
2. **## Pivot to the kit** — explain the architectural decision: legacy `_prototype/admin-*.html` is dark-themed and contradicts SKILL.md (light theme is default for clinical surfaces); v2 builds on the kit's `Sidebar.jsx`, `TopBar.jsx`, `settings.html` instead.
3. **## Two clinics** — table with id, display_name, timezone, contact_phone for both `northeast-denture-clinic` (Northeast Denture Clinic, +15879738089) and `market-mall-denture` (Market Mall Denture Clinic, +13682990959).
4. **## Owner persona** — name `Gia Huy`, email `giahuy.l.hoang@gmail.com`, role `Owner`, `assigned_clinic_ids: ["northeast-denture-clinic", "market-mall-denture"]`.
5. **## Files touched (additive)** — list:
   - `data/clinics.js` (rewrite — 2 clinics)
   - `data/users.js` (rewrite — owner + 2 staff)
   - `data/ai_config.js` (new)
   - `lib/auth.js` (additive — setCurrentClinic, getCurrentClinicId, getAssignedClinicIds, clinic-changed event)
   - `ui_kits/website/Sidebar.jsx` (additive — clinic switcher pill)
   - `ui_kits/website/TopBar.jsx` (additive — profile dropdown popover)
   - `ui_kits/website/settings.html` (additive — 4 new tabs: AI Greeting, AI Routing, AI Services, AI Knowledge)
   - `ui_kits/website/login.html` (one copy line: "Sign in to your clinic" → "Sign in to your workspace")
6. **## DOM hooks** — list every required `id=` and `data-` attribute (`rrd-clinic-switcher`, `rrd-clinic-switcher-menu`, `rrd-profile-pill`, `rrd-profile-menu`, `data-clinic-id`).
7. **## AI tab verbatim copy** — the four blocks of binding copy, one section per tab. Quote each verbatim string in fenced code blocks so they cannot be mis-copied.
8. **## Out of scope** — legacy `_prototype/admin-*.html`, dental-agent auth changes, migrating other `data/*.js` to new clinic ids.
9. **## Phase 0 v3** — note that this file IS Phase 0; later phases will produce the data files, chrome edits, tab additions, and verification.

## Verbatim required (must appear in the file)

- `Pivot to the kit`
- `northeast-denture-clinic`
- `market-mall-denture`
- `Northeast Denture Clinic`
- `Market Mall Denture Clinic`
- `Gia Huy`
- `giahuy.l.hoang@gmail.com`
- `AI Greeting`
- `AI Routing`
- `AI Services`
- `AI Knowledge`
- `data/ai_config.js`
- `Sign in to your workspace`
- `rrd-clinic-switcher`
- `rrd-profile-pill`
- `Phase 0 v3`

## Success criteria

- File size between 4 KB and 24 KB.
- All verbatim strings present.
- File is valid markdown (begins with `# `).
- No emoji anywhere in the file.

## Constraints

- Light, calm, clinical voice. Mirror SKILL.md tone.
- Definite article on system names: *The Sidebar. The Profile menu. The Settings panel.*
- No hype words ("AI-powered", "world-class", "seamless"). Concrete specifics only.
