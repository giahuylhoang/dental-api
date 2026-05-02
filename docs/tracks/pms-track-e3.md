# PMS Module E3 — Patients: DataTable + Patient360 redesign

Make `make test-pms-e3` exit 0.

## Why

PatientList is a basic table with 0 D1 imports. Patient360 is functional but feels like a wireframe. Both need real shadcn polish.

## Success criteria

### `frontend/src/features/patients/PatientList.tsx` — rewrite

- PageHeader — title "Patients", description "{N} active"; right: `<Button>+ New patient</Button>` (opens existing QuickBook flow as a `<Dialog>`).
- Toolbar `<Card>` with: D2 `<PatientSearchInput>` (left, full-width), filter `<Select>` for status (active / inactive / all), `<Select>` for provider.
- Main `<DataTable>` (E0): cols = name (with `<Avatar>`/initials chip), phone, dob, last visit, status `<Badge>`, actions `<DropdownMenu>` with "View / Edit / Archive" items. Sortable headers. Click row → navigate to `/patients/:id`.
- Pagination via `<DataTable>`'s built-in (or simple Prev/Next `<Button>`s).
- Empty state if no patients.

### `frontend/src/features/patients/Patient360.tsx` — rewrite

- **Sticky top header** within the page: D2 `<PatientChip variant="card">` (large avatar + name + phone + dob), then a row of Tabs.
- **Layout: left rail tabs + right content** (use D1 `<Tabs>` with `orientation="vertical"` if Radix supports it; otherwise the design system's Tabs primitive).
- Tabs: Overview / Appointments / Documents / Insurance / Treatment Plans / Lab Cases / Communications / Notes.
- Each tab content area is a `<Card>` wrapping the existing tab's data (we keep functionality the same — only chrome changes).
- Add an "Actions" `<DropdownMenu>` in the header: New appointment / Send message / Print summary / Archive.

## Tests first (`frontend/tests/track_pms_e3/`)

1. **`patients-redesign.test.tsx`** — render PatientList with mocked `/api/patients`; assert PageHeader, search input testid, DataTable with rows, "+ New patient" button.

2. **`patient360-tabs-redesign.test.tsx`** — render `Patient360` with mock patient; assert sticky header has `data-testid="patient-chip"`, all 8 tabs present.

3. **`patient-list-row-click-navigates.test.tsx`** — click a row; assert `useNavigate` called with `/patients/<id>`.

## Strict gate

- `PatientList.tsx` ≥3 ui imports.
- `Patient360.tsx` ≥3 ui imports.
- Zero raw `<button` in `PatientList.tsx`.

## Constraints

- Don't break P1 Patient360 tab content tests — only the chrome changes.
- The QuickBook flow continues to use the existing `/api/v2/clinical/patients/quick-book` endpoint.

```bash
make test-pms-e3
```
