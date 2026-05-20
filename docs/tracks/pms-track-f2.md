# PMS Module F2 — Billing: real list + invoice PDF (TDD)

Make `make test-pms-f2` exit 0.

## OSS

- `@tanstack/react-table` (MIT) — sortable, headless data table.
- `@react-pdf/renderer` (MIT) — declarative React PDF.

## Success criteria

- `/billing` (`InvoiceList.tsx`) renders a `@tanstack/react-table` with sortable columns:
  - Invoice # (`invoice_number`)
  - Patient (display name from invoice.patient_name; fall back to id)
  - Status pill (existing styling — keep the colors)
  - Total ($N.NN computed from `total_cents/100`)
  - Age (days since `created_at`)
- Status filter dropdown (existing M5) stays at the top.
- Fuzzy search input (existing M5) stays at the top.
- Click row → opens existing `InvoiceDrawer` (already built in P5).
- `InvoiceDrawer` adds a "Download PDF" button. Click → calls `pdf(<InvoicePdf invoice={inv} />).toBlob()` → `URL.createObjectURL(blob)` → opens in new tab. Filename `invoice-{invoice_number}.pdf` via `<a download={...}>`.
- F0's mock seed (`seedInvoices`) ensures ≥10 invoices visible on first paint.

## Tests first (`frontend/tests/track_pms_f2/`)

1. **`invoice-list-renders-seeded.test.tsx`** — render `<InvoiceList />` with MSW returning 12 fixture invoices; assert table has 12 data rows.

2. **`sort-by-total-works.test.tsx`** — render with 3 invoices of totals 100/500/250; click the "Total" header; assert rows order to 500/250/100 (descending). Click again → ascending.

3. **`invoice-pdf-renders.test.tsx`** — call `pdf(<InvoicePdf invoice={fixture} />).toBlob()`; assert `blob.size > 0` and `blob.type === 'application/pdf'`. (Use `@react-pdf/renderer`'s `pdf()` API.)

4. **`download-pdf-button-on-drawer.test.tsx`** — render `<InvoiceDrawer invoice={fixture} onClose={fn} />`; assert a button with text matching `/download.*pdf/i` is present; click it; assert `pdf(...).toBlob()` was invoked (or that `URL.createObjectURL` was called via spy).

## Implementation

- Modify: `frontend/src/features/billing/InvoiceList.tsx` — replace current table with `@tanstack/react-table` `useReactTable` + `flexRender`. Keep top filter row + search untouched.
- Modify: `frontend/src/features/billing/InvoiceDrawer.tsx` — add Download PDF button.
- New: `frontend/src/features/billing/InvoicePdf.tsx` — exports a React component:
  ```tsx
  import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';
  export default function InvoicePdf({ invoice }) {
    return <Document><Page>...</Page></Document>;
  }
  ```
  Show: clinic header, invoice_number, date, patient name, line items table (description, qty, unit_price, line_total), subtotal, tax, total, status. Pure layout — no fetches.

## Constraints

- Don't break M5 fuzzy search test (`frontend/tests/track_pms_m5/invoice-fuzzy-search.test.tsx`).
- Don't break P5 InvoiceDrawer tests (`frontend/tests/track_pms_p5/`).
- `@react-pdf/renderer` ships its own font registry — ship with default Helvetica (no custom font files).
- Sorting state stays in component-local state; no URL persistence needed.

```bash
make test-pms-f2
```
