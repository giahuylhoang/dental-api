# T05 — Dental components (Phase B)

## Objective
Port 28 dental-domain components from `/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/*.jsx` (PascalCase only — IGNORE `_prototype/`) into `/Users/giahuyhoangle/Projects/dental-api/web/components/dental/` as TypeScript. Add `LockedFeature.tsx`.

## Components
AppointmentCard, Avatar, Breadcrumb, CalendarGrid, ChartCard, CTA, DataTable, Drawer, EmptyState, FilterChips, FormField, Hero, IconButton, KanbanBoard, KpiTile, LabPipeline, LoginCard, MoneyCell, MonoText, Nav, PatientCard, Philosophy, Pillars, SearchInput, Sidebar, StatusPill, Tabs, ToothChartTile, TopBar.

## Rules
1. Convert each `.jsx` → `.tsx` with a typed `Props` interface. Preserve prop names; infer types from usage.
2. **No inline styles.** Replace every `style={{ ... }}` with Tailwind classes consuming token vars (e.g., `bg-card`, `text-foreground`, `border-border`, `bg-sidebar text-sidebar-foreground`, `text-muted-foreground`, `text-destructive`, `bg-primary text-primary-foreground`).
3. **No raw hex.** All colors via tokens.
4. Replace inline SVG icons with `lucide-react` imports where 1:1 (Sidebar nav: `LayoutGrid, Users, Calendar, ClipboardList, FlaskConical, DollarSign, MessageSquare, UserPlus, BarChart3, Phone, Settings`).
5. Replace `<a href="dashboard.html">`-style links with `next/link` and a route map (`href="/dashboard"`, `/patients`, `/schedule`, `/lab`, `/billing`, `/communications`, `/crm`, `/plans`, `/reports`, `/settings`). Sidebar should accept the active path via `usePathname()` (`"use client"`).
6. Add `"use client";` to any component using state, refs, event handlers, hooks, or browser APIs.
7. `Sidebar.tsx` widths: expanded `w-60` (240px), collapsed `w-16` (64px). `TopBar.tsx` height: `h-16`. `LoginCard.tsx` is dark-themed (relies on `.dark` scope from `(portal)` layout — do not toggle dark inside the component).
8. Import shadcn primitives from `@/components/ui/*` where appropriate (e.g., `Drawer.tsx` wraps `Sheet`, `Tabs.tsx` wraps Radix tabs, `DataTable.tsx` wraps the shadcn data-table). If a primitive isn't available, compose Radix directly.

## LockedFeature.tsx
Create `web/components/dental/LockedFeature.tsx`:
```tsx
import Link from "next/link";

export interface LockedFeatureProps {
  title: string;
  body: string;
  backHref: string;
  backLabel?: string;
}

export function LockedFeature({ title, body, backHref, backLabel = "Back" }: LockedFeatureProps) {
  return (
    <section className="bg-card text-card-foreground border border-border rounded-lg shadow-md p-8 max-w-2xl">
      <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
        Engineering Decision: Locked
      </span>
      <h2 className="mt-3 font-display text-2xl">{title}</h2>
      <p className="mt-3 text-muted-foreground max-w-prose">{body}</p>
      <Link
        href={backHref}
        className="mt-6 inline-flex items-center text-sm text-primary hover:underline"
      >
        ← {backLabel}
      </Link>
    </section>
  );
}
```

## Verify
```
cd web && npx tsc --noEmit && npx next build
```

## Done when
- All 28 components plus `LockedFeature.tsx` exist under `web/components/dental/`.
- `! grep -RIn 'style={{' web/components/dental` is empty.
- `! grep -RInE '#[0-9A-Fa-f]{3,8}\b' web/components/dental` is empty.
- `tsc --noEmit` and `next build` clean.
