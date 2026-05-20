# PMS Module D4 — Apply primitives to existing pages (visual upgrade pass)

Make `make test-pms-d4` exit 0.

## Why

D1–D3 created the primitives. D4 migrates existing pages to use them. **Strict primitive substitution** — no layout overhaul, no new features, no copy changes.

## Success criteria

For each file below, replace ad-hoc Tailwind elements with D1 primitives:

| Page | Substitutions |
|---|---|
| `Dashboard.tsx` | KPI cards → `<Card>`, "View" actions → `<Button>` |
| `PatientList.tsx` | Search → `<Input>` (already replaced by D2 search? confirm), table actions → `<Button>` |
| `InvoiceList.tsx` | "New Invoice" → `<Button>`, status pills → `<Badge>` (variant by status), search → `<Input>` |
| `InvoiceDrawer.tsx` | All buttons → `<Button>`, panels → `<Card>` |
| `LabCaseKanban.tsx` | Cards → `<Card>`, status pills → `<Badge>`, "Loading" → `<Skeleton>` (if not already) |
| `LabCaseDrawer.tsx` | Buttons → `<Button>`, tabs → `<Tabs>` |
| `LeadKanban.tsx` | Cards → `<Card>`, source pills → `<Badge>`, skeletons → `<Skeleton>` |
| `LeadDrawer.tsx`, `LeadCreateDialog.tsx` | Dialog → `<Dialog>`, buttons → `<Button>`, inputs → `<Input>` |
| `CommInbox.tsx`, `ThreadList.tsx`, `ThreadDetail.tsx` | Buttons → `<Button>`, channel chips → `<Badge>`, unread dots → `<Badge>` |
| `ComposeDialog.tsx` | Dialog → `<Dialog>`, segmented control = 3 `<Button variant="outline" / "default">`, send → `<Button>` |
| `TreatmentPlansPage.tsx`, `TreatmentPlanEditor.tsx` | Status pills → `<Badge>`, transition buttons → `<Button>`, item rows in `<Card>` |
| `Scheduler.tsx`, `NewAppointmentDialog.tsx`, `AppointmentDrawer.tsx` | Dialog → `<Dialog>`, buttons → `<Button>` |
| `SettingsPage.tsx` and 4 cards | Sections in `<Card>`, save → `<Button>`, inputs → `<Input>` |

Use `lucide-react` icons in place of any current emoji or text-based icons (e.g., the channel toggle `📱 / ✉️ / 💬` may stay as emoji *inside* the button label since they're domain-symbolic — use lucide for navigation/action icons like Plus, Trash, Edit, X, ChevronDown).

## Tests first (`frontend/tests/track_pms_d4/`)

1. **`dashboard-uses-ui-button.test.tsx`** — render Dashboard; assert at least one element with the cva button root class is present (e.g., a class matching `inline-flex items-center justify-center` from D1's button cva).

2. **`invoice-list-renders-with-ui-input-search.test.tsx`** — render; assert search input is the `<Input>` from D1 (use `data-testid` or check `className`).

3. **`lab-kanban-cards-include-patient-chip.test.tsx`** — render with seeded cases; assert every card has `data-testid="patient-chip"` (D2).

4. **`lead-kanban-uses-skeleton-from-d1.test.tsx`** — render with delayed query; assert skeletons are the D1 `<Skeleton>` (check class or testid).

5. **`compose-dialog-uses-d1-dialog.test.tsx`** — open compose; assert the dialog has Radix data attributes (e.g., `data-state="open"`).

## Constraints

- **No layout changes.** Pages keep their current visual structure.
- All previous tests must still pass — if any breaks, you must update the test (preserving its intent) rather than reverting the migration.
- Don't introduce new features. Don't reorder fields. Don't change copy.
- Lint must stay green.

```bash
make test-pms-d4
```
