# PMS Module E4 — Lab + Treatment Plans: real Cards + drag affordance

Make `make test-pms-e4` exit 0.

## Why

LabCaseKanban: 0 D1 imports + 2 ad-hoc card classes (`rounded ... border ... bg-white`). TreatmentPlanEditor: still uses a plain table.

## Success criteria

### `frontend/src/features/lab/LabCaseKanban.tsx` — rewrite

- PageHeader — title "Lab", description "{N} active cases"; right: `<Button>+ New case</Button>` (opens existing LabCaseCreateForm in a D1 `<Dialog>`).
- Status legend row using `<Badge>`s.
- 5 columns (draft / sent / in_progress / returned / remake). Each column has a sticky header with status name + count.
- Each card is a D1 `<Card>` with:
  - `<CardHeader>` — case_number monospace + status `<Badge>` right.
  - `<CardContent>` — D2 `<PatientChip variant="inline">`, vendor name (small), due date (small with calendar icon).
  - `<CardFooter>` — quick-action `<DropdownMenu>` (Send / Mark returned / Request remake) on hover.
- Drag handle visible on hover (using existing dnd-kit setup).

### `frontend/src/features/lab/LabCaseDrawer.tsx` — D1 Sheet

- Use D1 `<Sheet>` (E0) sliding from the right.
- Header: D2 `<PatientChip variant="card">` (the patient), case_number, vendor, status `<Badge>`.
- Tabs (D1 `<Tabs>`): Detail / Implants / Materials / Events.
- Each tab in a `<ScrollArea>` if content is long.

### `frontend/src/features/treatment-plans/TreatmentPlansPage.tsx` — list polish

- PageHeader, toolbar `<Card>` (search + status filter + new-plan button).
- `<DataTable>` for plans: patient name (PatientChip), title, status Badge, total estimate, actions DropdownMenu.

### `frontend/src/features/treatment-plans/TreatmentPlanEditor.tsx` — rewrite

- PageHeader with the plan title + sticky D2 PatientChip header card + status `<Badge>`.
- D1 `<Tabs>`: Items / Tooth Chart / Care Notes / History.
- Items tab: `<DataTable>` of items with inline edit; care_notes via existing tiptap.
- Tooth Chart tab: existing ToothChart wrapped in `<Card>`; clicking a tooth shows a D1 `<Tooltip>` with that tooth's items.
- Status transitions are D1 `<Button>`s in a footer row (e.g., "Present", "Accept", "Mark in progress", "Complete", "Decline" — visibility per current status).

## Tests first (`frontend/tests/track_pms_e4/`)

1. **`lab-tp-redesign.test.tsx`** — render LabCaseKanban; assert ≥5 columns, each card has data-testid="patient-chip", D1 Card classes present.

2. **`lab-drawer-uses-sheet.test.tsx`** — open drawer; assert Radix Sheet data-attr.

3. **`treatment-plan-editor-tabs.test.tsx`** — render editor; assert 4 D1 Tabs visible.

4. **`treatment-plan-editor-status-buttons.test.tsx`** — for a draft plan, assert "Present" button visible; for accepted plan, "Mark in progress" visible.

## Strict gate

- `LabCaseKanban.tsx` ≥3 ui imports.
- `TreatmentPlanEditor.tsx` ≥3 ui imports.
- Zero ad-hoc card classes in `LabCaseKanban.tsx`.

## Constraints

- Don't break P3 + M3 + F3 + F4 tests.
- Drag-and-drop semantics remain (dnd-kit on the kanban; drop fires PATCH `/api/v2/lab/cases/:id/status`).

```bash
make test-pms-e4
```
