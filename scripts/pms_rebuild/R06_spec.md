# R06 — /billing from billing.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/billing.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/billing/page.tsx` (**fully replace** — current detail-drawer version is wrong)

## Composition
This is a **list page**, not a detail-drawer page:
1. Page header with **Export ledger / + New claim / + New invoice** buttons.
2. **4-column KPI strip**: Outstanding, Overdue 30+, Collected 30d, Claims open.
3. **A/R aging visualization**: bar-chart grid (0-30, 31-60, 61-90, 90+ buckets).
4. **Invoices table**: Invoice # (mono) / Patient / Issued / Due / Total / Status.
5. **Insurance claims table** below invoices.
6. Drawer for invoice/claim detail when row clicked (this part can stay close to existing InvoiceDrawer code).

## Data wiring
- Invoices → `/api/v2/billing/invoices`.
- Claims → `/api/v2/billing/claims` if exists; else seed with TODO.
- A/R aging → `/api/v2/reporting/ar-aging` if exists; else seed with TODO.

## Done when
- Page is the list-with-summary layout, not the detail-drawer app.
- A/R aging visualization renders.
- Two stacked tables (invoices, claims) present.
- `cd web && npx next build` green.
