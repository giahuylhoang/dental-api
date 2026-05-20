# T03 — shadcn/ui primitives (Phase A)

## Objective
Port shadcn primitives from `/Users/giahuyhoangle/Projects/dental-api/frontend/src/components/ui/` to `/Users/giahuyhoangle/Projects/dental-api/web/components/ui/`, wired to the new tokens (no raw hex, no inline styles).

## Files to port (all under `web/components/ui/`)
`badge, button, card, command, data-table, dialog, dropdown-menu, input, page-header, popover, scroll-area, select, separator, sheet, skeleton, sonner, switch, tabs, textarea, toast, toaster, tooltip` — each `.tsx`. Also port `use-toast.ts` if it exists in the Vite app.

## Rules
1. Read the corresponding file in `frontend/src/components/ui/` and produce an equivalent file in `web/components/ui/`. Preserve the public API (named exports + prop names) so feature pages can import without churn.
2. Add `"use client";` to the very first line of any file that uses Radix primitives, hooks, refs, or event handlers.
3. Replace any color literals with token classes:
   - `bg-background text-foreground`
   - `bg-card text-card-foreground border-border`
   - `bg-primary text-primary-foreground`
   - `bg-destructive text-destructive-foreground`
   - `ring-ring`, `bg-muted text-muted-foreground`, `bg-accent text-accent-foreground`
4. `button.tsx` — add a CVA `sweep` variant whose styles map to the `.btn .btn-primary .btn-md` utility chain in `web/styles/design-tokens.css`. Default variant remains `bg-primary text-primary-foreground`.
5. `lib/utils.ts` — port the `cn()` helper from `frontend/src/lib/utils.ts` (or create one if missing): `import { clsx } from 'clsx'; import { twMerge } from 'tailwind-merge'; export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }`.
6. Imports inside ported components must use the `@/components/...` and `@/lib/utils` aliases.
7. No inline styles. No raw hex.

## Sonner / Toast
- Keep both `sonner.tsx` (sonner Toaster) and `toast.tsx` + `toaster.tsx` + `use-toast.ts` (Radix toast) so feature code can use either, matching today's Vite app.

## Verify
```
cd web && npx tsc --noEmit && npx next build
```

## Done when
- All listed primitives exist under `web/components/ui/`.
- `cn()` exported from `web/lib/utils.ts`.
- `tsc --noEmit` and `next build` clean.
- No raw hex / inline styles in the ported files (run grep guard).
