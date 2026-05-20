# T10 — /lab + /billing

## Objective
Lab Kanban + drawers; invoice list + drawer + PDF preview + claim flows.

## References
- Visual: `ui_kits/website/{lab.html,lab-case-detail.html,denture-case-detail.html,billing.html,invoice-detail.html}`
- Logic: `frontend/src/features/lab/*` and `frontend/src/features/billing/*`

## /lab
- `web/app/(app)/lab/page.tsx` (`"use client"`).
- Use `KanbanBoard` from `@/components/dental/KanbanBoard` + dnd-kit.
- Columns by case status (sent → wax-up → tried-in → completed).
- LabCaseDrawer + DentureCaseDrawer (Sheet).
- Forms: LabCaseCreateForm, ImplantForm, MaterialConsumptionForm — react-hook-form + zod.
- Endpoints unchanged (mirror current code).

## /billing
- `web/app/(app)/billing/page.tsx` (`"use client"`).
- DataTable of invoices with search + date range.
- InvoiceDrawer (Sheet) with editor.
- InvoicePdf via `@react-pdf/renderer`: dynamic import (`{ ssr: false }`); `pdf().toBlob()` for download. Inline styles ARE allowed inside `*Pdf*` components only (PDF library requires them).
- ClaimDrawer + SubmitClaimForm + AdjudicateForm.

## Verify
```
cd web && npx tsc --noEmit && npx next build
```
