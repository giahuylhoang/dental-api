# PMS Track P5 — Billing detail drawer + claim linkage

You are kiro-cli running headless. Make invoices inspectable, link insurance claims, surface adjudication. Gate: `make test-pms-p5`.

## Deliverable files

- `frontend/src/features/billing/InvoiceDrawer.tsx`
  - Props: `{ invoiceId: string | null, open, onClose, onChanged }`
  - Loads via `GET /api/v2/billing/invoices/{id}` (or list w/ filter if no detail GET)
  - Sections: header (patient, status, totals), Lines table (description, qty, unit_price_cents, total), Payments list, Claims list
  - Action buttons (gated by status):
    - "Issue" (status=draft) → POST /issue
    - "Record Payment" → opens form (method, amount_cents, ref?) → POST /payments
    - "Void" (status≠paid) → confirm → POST /void
    - "Submit Claim" → opens `SubmitClaimForm`

- `frontend/src/features/billing/SubmitClaimForm.tsx`
  - Inside drawer; fields: carrier (select from existing patient insurance), kind (predetermination|claim)
  - POST `/api/v2/insurance/claims` body `{invoice_id, carrier, kind}` → on success, opens `ClaimDrawer` for the new claim

- `frontend/src/features/billing/ClaimDrawer.tsx`
  - Props: `{ claimId: string | null, open, onClose, onChanged }`
  - Loads claim via `GET /api/v2/insurance/claims/{id}`
  - Sections: status timeline, response codes (list), adjudication form (when status=submitted)
  - Buttons: "Submit" (status=draft) → POST /submit, "Mark paid" (status=adjudicated) → POST /mark-paid

- `frontend/src/features/billing/AdjudicateForm.tsx`
  - Props: `{ claimId: string, onSaved }`
  - Fields: outcome (accepted|rejected|partial), accepted_amount_cents (if accepted/partial), notes
  - POST `/api/v2/insurance/claims/{id}/adjudicate`

- Modify `frontend/src/features/billing/InvoiceList.tsx`:
  - Row click → opens InvoiceDrawer
  - Add a `denture_case_id` optional select on the new-invoice form (lists patient's denture cases)
  - URL search params: `/billing?status=overdue` filters by status; honor it on mount

- Modify `frontend/src/features/dashboard/Dashboard.tsx` (or `frontend/src/features/reporting/Dashboard.tsx`, whichever exists):
  - The "A/R aging" tile becomes a Link to `/billing?status=overdue`

## Tests

Vitest (`frontend/tests/track_pms_p5/`):
- `invoice-drawer.test.tsx` — renders, Issue button POSTs
- `claim-drawer.test.tsx` — adjudicate form posts correct body
- `submit-claim.test.tsx` — opens claim drawer after submit

Playwright (`frontend/e2e/track_pms_p5/billing-flow.spec.ts`):
- Login → /billing → click invoice → drawer opens → record payment → balance updates → submit claim → claim drawer → adjudicate accepted → mark paid

## Constraints

- Reuse `Drawer`, `FormField`, `DateTimePicker` (from P1/P2).
- Don't break the existing payment-recording modal behavior; deprecate it gracefully if InvoiceDrawer fully replaces it.

## Commands

```bash
cd frontend && npm run lint && npm run build
cd frontend && npm run test:pms-p5
cd frontend && npm run e2e:pms-p5
make test-pms-p5
```

When `make test-pms-p5` exits 0, you are done.
