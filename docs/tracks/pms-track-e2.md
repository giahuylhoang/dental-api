# PMS Module E2 — Dashboard: real shadcn admin layout

Make `make test-pms-e2` exit 0.

## Why

Current Dashboard is bare-bones KPI tiles + a couple of `<SimpleBar>` charts. We need a real admin-dashboard layout with proper hierarchy, an activity table, and empty states.

## Success criteria

### `frontend/src/features/reporting/Dashboard.tsx` — rewrite

Layout (top to bottom):

1. **PageHeader** — title "Dashboard", description "Last updated <relative time>"; right: D1 `<Button variant="outline">` "Date range" (no functionality this round, just a styled placeholder), `<Button>` "Export" (no-op).
2. **KPI tile grid (4 cols on lg, 2 on md, 1 on sm)** — each tile is a D1 `<Card>`:
   - `<CardHeader>` with small label (`text-sm text-muted-foreground`) + a small lucide icon (top-right).
   - `<CardContent>` with big number (`text-2xl font-semibold`).
   - `<CardFooter>` with tiny trend indicator (placeholder for now: `<Badge variant="success">+12%</Badge>` if production tile, `<Badge variant="destructive">+0.4%</Badge>` for no-show).
   - Tiles: Production this month / No-show rate / Lab cost per case / A/R balance.
3. **A/R Aging row** — `<Card>` with `<CardHeader>{title:"A/R Aging", action: <Button variant="link">View overdue invoices</Button>}</CardHeader>`; `<CardContent>` shows 4 bucket sub-cards in a flex row, each with bucket label + amount.
4. **Two-column row**: 
   - **Left: "Production by Provider"** `<Card>` — replace the home-rolled SimpleBar with D1 `<DataTable>` (E0) showing provider_name + production columns, sortable.
   - **Right: "Remake Rate by Lab"** `<Card>` — same `<DataTable>` shape: lab_name, total_cases, remake_rate (formatted as %).
5. **Recent activity** `<Card>` — `<DataTable>` of recent appointments / invoices / leads (pull from existing endpoints — appointments today + invoices last 7d + leads last 7d, merge client-side, top 10). Cols: time, type icon (Lucide), description, status `<Badge>`. Empty state if no rows.

All zero values render with a muted style (e.g., `<span className="text-muted-foreground">—</span>` instead of "$0.00"); empty data → `<EmptyState>` (use D0 reference if available, otherwise a small `<Card>` with icon + "No data yet" + "View {{module}}" link).

## Tests first (`frontend/tests/track_pms_e2/`)

1. **`dashboard-redesign.test.tsx`** — render with mocked KPI / production / remake responses; assert:
   - PageHeader title "Dashboard" present.
   - 4 KPI tiles present (each is a `<Card>` with data-testid="kpi-tile").
   - A/R Aging Card present with 4 buckets.
   - Two DataTables (Production by Provider + Remake Rate) present.
   - "Recent activity" section present.

2. **`dashboard-empty-state.test.tsx`** — mock all reporting endpoints to return empty arrays / zeros; assert empty-state cards render and don't crash.

3. **`dashboard-uses-card-and-datatable.test.tsx`** — assert DOM contains ≥6 elements with the D1 Card root class and ≥2 elements with the DataTable testid.

## Strict gate

- `Dashboard.tsx` must have ≥4 `from '@/components/ui'` imports.
- Zero raw `<button` in `Dashboard.tsx`.
- Zero ad-hoc card classes (`rounded.*border.*bg-white`).

## Constraints

- Reuse the existing reporting endpoints — don't add new ones.
- A/R aging "View overdue invoices" link goes to `/billing?status=overdue` (existing query param).

```bash
make test-pms-e2
```
