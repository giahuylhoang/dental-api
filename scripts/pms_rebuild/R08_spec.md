# R08 — /crm from crm.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/crm.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/crm/page.tsx` (overwrite)

## Composition
1. Page title "CRM · Leads" (or whatever the HTML uses verbatim).
2. **4-column KPI strip**: Active leads, Converted 30d, Conversion rate, Avg time to first contact.
3. **Kanban board** with the exact stage columns and blue-dot stage indicators from the HTML. Lead cards include source badge, owner avatar, notes preview.
4. Lead detail drawer with tabs and **"Convert to patient"** + Archive buttons.

## Data wiring
- Leads → `/api/leads` (existing).
- Activities → `/api/leads/{id}/activities` (existing).
- Convert → POST `/api/leads/{id}/convert` if exists; else seed/TODO.

## Done when
- Kanban + KPI strip + lead detail drawer all present.
- `cd web && npx next build` green.
