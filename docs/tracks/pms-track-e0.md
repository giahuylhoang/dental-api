# PMS Module E0 — Foundation: missing primitives + HSL token bridge

Make `make test-pms-e0` exit 0.

## Why

D4 was sloppy — the gates were too thin so kiro got them green without actually migrating most pages (audit shows 0 D1 imports in Scheduler, PatientList, CommInbox, LabCaseKanban). E0 lays down the missing primitives + a HSL token bridge so the next 6 modules can do *real* shadcn-grade redesigns with strict gates.

## OSS to install

- `sonner` (MIT) — modern toast library used in shadcn ecosystem (replace the underused Radix toast with sonner — better DX).
- `@radix-ui/react-tooltip` (MIT)
- `@radix-ui/react-scroll-area` (MIT)
- `@radix-ui/react-separator` (MIT)
- `react-resizable-panels` (MIT) — used by E5 for the comms inbox split view.

## Success criteria

- New `frontend/src/components/ui/sheet.tsx` — wraps `@radix-ui/react-dialog` as a Sheet (slide-from-side; sides: top/bottom/left/right). Used by E5 for mobile sidebar + Patient360 left rail.
- New `frontend/src/components/ui/separator.tsx` — wraps `@radix-ui/react-separator`.
- New `frontend/src/components/ui/scroll-area.tsx` — wraps `@radix-ui/react-scroll-area` with shadcn styling.
- New `frontend/src/components/ui/tooltip.tsx` — wraps `@radix-ui/react-tooltip` (TooltipProvider, Tooltip, TooltipTrigger, TooltipContent).
- New `frontend/src/components/ui/sonner.tsx` — Sonner `<Toaster />` styled to match the design system (dark/light variants reading from CSS vars). Mount once in `App.tsx`.
- New `frontend/src/components/ui/data-table.tsx` — generic `<DataTable columns={...} data={...} />` built on `@tanstack/react-table` (already installed) with sortable headers, hover rows, row selection slot, empty state. Used by E2/E3/E5.
- New `frontend/src/design_system/tokens-hsl.css` — re-declare each base color as `--ds-action: 217 91% 50%;` (HSL triplets, no `hsl()` wrapper) so Tailwind's alpha modifiers work (`bg-action/50`).
- Modify `frontend/tailwind.config.js` to use `'hsl(var(--ds-action) / <alpha-value>)'` form for every semantic color (`primary`, `secondary`, `destructive`, `accent`, `muted`, `card`, `popover`, `border`, `input`, `ring`).
- Modify `frontend/src/index.css` to also `@import './design_system/tokens-hsl.css'` after the existing tokens import.
- Update `frontend/src/components/ui/index.ts` barrel to export every new primitive.
- New ESLint custom rule (or just an entry in `.eslintrc` `no-restricted-syntax` / `no-restricted-properties`) that flags **ad-hoc card classes** in `.tsx` files (regex `rounded-(?:lg|md)\s+border\s+(?:border-zinc-\d+\s+)?bg-white`). Apply only inside `frontend/src/features/**`.
- Mount `<Toaster />` (sonner) and `<TooltipProvider>` in `frontend/src/App.tsx` once (wrapped around the route tree).

## Tests first (`frontend/tests/track_pms_e0/`)

1. **`foundation-primitives-exist.test.tsx`** — render each new primitive in isolation; assert it mounts without crashing.
2. **`hsl-tokens-allow-alpha.test.ts`** — read built CSS; assert at least one resolved `bg-primary/80` style produces an `rgba()` or `hsl(... / 0.8)` declaration.
3. **`sonner-toast-fires.test.tsx`** — call `toast('hi')` from `sonner`; assert toast text appears in DOM.
4. **`data-table-sortable.test.tsx`** — render `<DataTable columns={[{accessorKey:'total', header:'Total', enableSorting:true}]} data={[{total:1}, {total:3}, {total:2}]} />`; click "Total" header; assert rows reorder.
5. **`tooltip-shows-on-hover.test.tsx`** — render `<Tooltip><TooltipTrigger>hover</TooltipTrigger><TooltipContent>info</TooltipContent></Tooltip>`; fire mouse-enter; assert "info" visible.

## Constraints

- All previous tests must stay green (213/213 frontend, 185/185 backend).
- Don't break existing `<Toast>` wrappers (D1) — we keep them but Sonner is the new path; existing call sites can migrate gradually.
- Tokens-hsl bridge must not change any rendered color visibly (smoke check the showcase page).

```bash
make test-pms-e0
```
