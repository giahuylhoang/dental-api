# PMS Module M5 — Billing typeahead + ⌘K command palette (TDD)

Make `make test-pms-m5` exit 0.

## OSS

- `cmdk` (already installed) — Vercel's command palette primitive.
- `fuse.js` (already installed) — fuzzy matching.

## Success criteria

- `InvoiceList`: a search input above the status filter. Debounced (200ms). Fuzzy-matches against (invoice_number, patient_name, status, total_cents/100). Empty query shows everything.
- Global ⌘K (cmd-K on Mac, ctrl-K on others) opens `<CommandPalette />`. Mounted in the AppShell so it's available on every authenticated page.
- Palette sections: Invoices, Patients, Appointments, Quick actions ("New invoice", "New appointment", "New lead"). Each item Enter-key navigates / opens the right drawer.
- Recently viewed list (top of palette, persists in `localStorage` under key `pms.recentlyViewed`, max 10 items).

## Tests first (`frontend/tests/track_pms_m5/`)

1. **`invoice-fuzzy-search.test.tsx`** — render `<InvoiceList />` with mocked invoice list; type "ali" in search; assert visible rows include only ones with patient name containing Ali (case-insensitive fuzzy via Fuse).

2. **`command-palette-opens-on-cmdk.test.tsx`** — render an `<AppShell>` mock containing `<CommandPalette />`; fire `keydown` for `cmd+k`; assert palette element with `role="dialog"` is visible.

3. **`recently-viewed-persists.test.tsx`** — call helper `markVisited(kind: 'patient', id, label)`; mount palette; assert recently-viewed item appears at top.

E2E (`frontend/e2e/track_pms_m5/`):
- Login → press cmd+k → palette opens → type "alice" → Enter → URL becomes `/patients/<some-id>` → press cmd+k again → "alice" item appears at top under "Recently viewed".

## Implementation

- New: `frontend/src/features/search/CommandPalette.tsx` — uses `cmdk` (`Command`, `Command.Input`, `Command.List`, `Command.Group`, `Command.Item`). Listens for cmd+k via global keydown handler.
- New: `frontend/src/features/search/recentlyViewed.ts` — `markVisited`, `getRecent` localStorage helpers.
- Mount `CommandPalette` in `frontend/src/App.tsx` or a shared `AppShell` component (whichever exists).
- Modify: `frontend/src/features/billing/InvoiceList.tsx` — add fuzzy `<input>` + Fuse instance.

## Constraints

- Keep the existing status filter dropdown (don't replace it).
- Recently-viewed reads/writes must NOT throw if `localStorage` is unavailable (SSR or private mode safety).
- cmd+k handler must NOT trigger when an `<input>` or `<textarea>` is focused (typing CMD+K in a notes field shouldn't open the palette — wait, actually it SHOULD; this is the convention. But ESC should close it).

```bash
make test-pms-m5
```
