# PMS Module D1 — Runtime primitives + Tailwind bridge (shadcn-shape)

Make `make test-pms-d1` exit 0.

## Why

D0 created the static design-system reference. D1 brings the tokens *into* the live React runtime and ships the shadcn-shape primitives the rest of the app will consume.

## OSS to install

- `class-variance-authority` (MIT) — variant API
- `clsx` + `tailwind-merge` (MIT) — `cn()` helper
- `lucide-react` (ISC) — icons
- `@radix-ui/react-dialog`, `@radix-ui/react-popover`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-tabs`, `@radix-ui/react-toast`, `@radix-ui/react-select`, `@radix-ui/react-slot` (MIT)
- `tailwindcss-animate` (MIT)

(Do NOT install shadcn-cli — we hand-author the same shape so we own it.)

## Success criteria

- New `frontend/src/lib/utils.ts` exporting `cn(...inputs: ClassValue[]) => twMerge(clsx(inputs))`.
- New `frontend/src/components/ui/`:
  - `button.tsx` — variants `default | destructive | outline | secondary | ghost | link`, sizes `sm | default | lg | icon`. Uses `cva`. Supports `asChild` via `@radix-ui/react-slot`.
  - `input.tsx` — text/email/password/number, full-width, focus ring from action color.
  - `card.tsx` — `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`.
  - `dialog.tsx` — wraps `@radix-ui/react-dialog` with `Dialog`, `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter`, `DialogClose`. Backdrop blur, animate-in/out.
  - `popover.tsx` — wraps `@radix-ui/react-popover`.
  - `command.tsx` — built on existing `cmdk` (already installed). Exports `Command`, `CommandInput`, `CommandList`, `CommandEmpty`, `CommandGroup`, `CommandItem`.
  - `badge.tsx` — variants `default | secondary | destructive | outline | success | warning`.
  - `skeleton.tsx` — shimmering placeholder.
  - `tabs.tsx` — wraps `@radix-ui/react-tabs`.
  - `toast.tsx` + `toaster.tsx` + `use-toast.ts` — wraps `@radix-ui/react-toast`.
  - `select.tsx` — wraps `@radix-ui/react-select`.
  - `dropdown-menu.tsx` — wraps `@radix-ui/react-dropdown-menu`.
- Extend `frontend/tailwind.config.js`:
  - Add `theme.extend.colors`: `clinical: { 50..900 }`, `action: {...}`, `accent: {...}`, plus semantic aliases `border`, `input`, `ring`, `background`, `foreground`, `primary`, `secondary`, `destructive`, `muted`, `accent`, `popover`, `card` — each pointing to a CSS variable from D0 tokens (e.g., `'hsl(var(--color-action) / <alpha-value>)'` or direct `'var(--color-action)'`).
  - Add `theme.extend.borderRadius`: `lg: 'var(--radius-lg)'`, `md: 'var(--radius-md)'`, `sm: 'var(--radius-sm)'`.
  - Add `theme.extend.boxShadow`: similar.
  - Add `tailwindcss-animate` to `plugins`.
- Modify `frontend/src/index.css`:
  - At the top, add `@import '../design_system/dental-pms.v1/tokens.css';` (relative to the CSS file).
  - Keep existing Tailwind layers below.
- New `frontend/src/components/ui/_showcase.tsx` — a single page mounting every primitive with all variants. Wire it at route `/dev/ui` in `App.tsx` (only render in `import.meta.env.DEV`). This is the visual smoke test.
- New `frontend/src/components/ui/index.ts` — barrel that re-exports every primitive (consumers do `import { Button, Dialog } from '@/components/ui'`).

## Tests first (`frontend/tests/track_pms_d1/`)

1. **`cn-utility.test.ts`** — `import { cn } from '../../src/lib/utils'`. Assert `cn('a', false && 'b', 'p-4 p-6')` ===  string containing `'a'` and `'p-6'` (last wins via twMerge).

2. **`button-variants.test.tsx`** — render `<Button variant="destructive" size="sm">x</Button>`; assert root has classes matching the destructive variant + small size.

3. **`button-as-child-renders-anchor.test.tsx`** — `<Button asChild><a href="/x">Go</a></Button>`; assert rendered element is `<a>`, not `<button>`, and has the button classes.

4. **`dialog-opens-and-closes.test.tsx`** — wrap in `<Dialog>` with a trigger + content; click trigger; assert content visible. Press Escape; assert content gone.

5. **`command-mounts-cmdk.test.tsx`** — render `<Command><CommandInput placeholder="Search" /><CommandList><CommandItem>One</CommandItem></CommandList></Command>`; assert input is in the document and item visible.

6. **`badge-variants.test.tsx`** — assert `success` and `warning` variants render expected classes.

7. **`skeleton-renders-with-pulse.test.tsx`** — render `<Skeleton className="h-4 w-20" />`; assert it has `animate-pulse` (or your loading class).

## Implementation guidance

- Match shadcn/ui source as closely as possible (it's MIT — keep the same prop API and class names so future contributors can paste shadcn snippets without modification).
- For colors that need alpha (`bg-foreground/50`), use the `'hsl(var(--...) / <alpha-value>)'` pattern. If your D0 tokens are direct hex values, write a small companion `tokens-hsl.css` next to `tokens.css` that re-declares each color as HSL triplets.
- The `_showcase.tsx` page should be data-driven: a list of `{ title, render: () => JSX }` entries.

## Constraints

- All previous tests must still pass (P0–P5, M0–M6, F0–F6).
- Don't break the existing `frontend/src/index.css` Tailwind setup — only ADD an `@import` at the top.
- The showcase page is DEV-only — it must not be reachable in production builds.

```bash
make test-pms-d1
```
