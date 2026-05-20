# PMS Module E6 — CRM + Settings

Make `make test-pms-e6` exit 0.

## Success criteria

### `frontend/src/features/crm/LeadKanban.tsx` — rewrite

- PageHeader — title "CRM", desc "{N} active leads"; right: `<Button>+ New lead</Button>` (opens existing LeadCreateDialog in D1 Dialog).
- 5 columns (NEW / CONTACTED / QUALIFIED / CONVERTED / LOST). Sticky column headers with status name + count + tiny color indicator.
- Each card = D1 `<Card>`:
  - `<CardHeader>` — name + source `<Badge>`.
  - `<CardContent>` — phone (with phone icon), email (with mail icon), notes preview (line-clamp-2).
  - `<CardFooter>` — actions DropdownMenu (Convert / Edit / Add activity / Archive).
- Skeleton state when loading (already from D5 — keep).
- Empty column placeholder ("Drop leads here") when column empty.

### `frontend/src/features/crm/LeadDrawer.tsx` — D1 Sheet

- Replace the existing Drawer with D1 `<Sheet>`.
- Tabs: Detail / Activities / Convert.

### `frontend/src/features/settings/SettingsPage.tsx` — nav rail layout

- Replace the stacked-cards layout with a left **nav rail** + right **content panel** layout (sidebar 240px, content fluid).
- Nav rail: D1 `<Tabs orientation="vertical">` (or a list of `<Button variant="ghost">`s with active state) with sections: Clinic Info / Working Hours / Notifications / Integrations / Density.
- Content panel: only the selected section's `<Card>` is shown at a time.
- Each section uses `<Form>` + `<FormField>` + D1 `<Input>`/`<Select>`/`<Switch>` (add Switch primitive if missing).
- Save button at the bottom of each section's Card; dirty-state detection.

### Add primitive: `frontend/src/components/ui/switch.tsx`

Standard shadcn-shape switch wrapping `@radix-ui/react-switch` (install if not present).

## Tests first (`frontend/tests/track_pms_e6/`)

1. **`crm-settings-redesign.test.tsx`** — render LeadKanban; assert PageHeader, ≥3 ui imports, 5 columns, each card uses `<Card>` class.

2. **`lead-card-source-badge.test.tsx`** — render with leads of varied sources; assert each card has a source `<Badge>`.

3. **`settings-nav-rail.test.tsx`** — render SettingsPage; assert nav-rail items present (Clinic Info / Working Hours / Notifications / Integrations / Density); click "Working Hours"; assert that section's content visible and Clinic Info hidden.

4. **`settings-density-toggle-uses-switch.test.tsx`** — assert Density section has a D1 `<Switch>` (or Select) primitive with current value.

## Strict gate

- `LeadKanban.tsx` ≥3 ui imports.
- `SettingsPage.tsx` ≥3 ui imports.
- Zero raw `<button` in either.

## Constraints

- Don't break M4, F5, F6 tests.
- Settings still saves via PUT `/api/v2/settings/clinic` (no backend changes).
- Density toggle still writes `localStorage.pms.density` and `<html data-density>` (D5 contract preserved).

```bash
make test-pms-e6
```
