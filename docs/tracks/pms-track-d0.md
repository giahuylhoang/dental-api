# PMS Module D0 — Design system reference repo (mirror chaseglobal.com.v2)

Make `make test-pms-d0` exit 0.

## Why

We need a design-system source-of-truth that mirrors the proven chaseglobal.com.v2 layout — so every contributor finds tokens, components, and reference pages where they expect them. This module creates the static reference repo. The next module (D1) wires its tokens into the React runtime.

## Reference structure (mirror exactly)

`/Users/giahuyhoangle/Projects/chaseglobal.com/design_systems/chaseglobal.com.v2/` is laid out as:
```
chaseglobal.com.v2/
├── colors_and_type.css     # single master CSS-variable token file (~27KB)
├── README.md               # design philosophy, page templates, tone
├── SKILL.md                # Claude-skill metadata
├── assets/                 # logo + svgs grouped by domain
├── preview/                # ~22 standalone HTML reference pages (no JS — just <link>+inline tokens)
├── ui_kits/website/        # ~35 PascalCase .jsx flat components, *-data.js fixtures co-located
└── uploads/                # brand logo
```

Key conventions: flat (no atoms/molecules folders), one master CSS file, single-file PascalCase components, fixture data co-located, NO build tooling at the design-system layer.

## Success criteria

Create `frontend/design_system/dental-pms.v1/` containing:

- **`tokens.css`** — master file (≥10KB). `:root` CSS variables:
  - **Color base** — 10-shade ramps for `--ds-clinical` (clinical white/grey ramp), `--ds-action` (blue ramp), `--ds-accent` (teal ramp), `--ds-warn` (amber ramp), `--ds-danger` (red ramp). Each shade `50..900`.
  - **Color semantic** — `--color-text-primary`, `--color-text-secondary`, `--color-bg-canvas`, `--color-bg-clinical`, `--color-action`, `--color-action-hover`, `--color-success`, `--color-warning`, `--color-danger`, `--color-border-default`, `--color-border-subtle`.
  - **Typography** — `--font-display` (Inter), `--font-mono` (JetBrains Mono). Imported via Google Fonts `@import`. 10-step type scale `--text-xs..5xl`. 6 line-heights `--leading-{tight,snug,normal,relaxed,loose,display}`. 6 letter-spacings `--tracking-{tighter,tight,normal,wide,wider,widest}`.
  - **Spacing** — `--space-1..32` (14 steps; `0.25rem`–`8rem`).
  - **Radii** — `--radius-{none,sm,md,lg,xl}`.
  - **Shadows** — `--shadow-{xs,sm,md,lg,xl,2xl,inset}`.
  - **Motion** — `--ease-{out,in,in-out}` and `--duration-{fast,base,slow,slower}`.
- **`README.md`** — ≥3KB. Section headings: "Design philosophy", "Page templates", "Color story", "Type system", "Spacing & rhythm", "Component principles", "Tone of voice". Frame: clinical clean / calm-confident / glanceable / forgiving (long shifts).
- **`SKILL.md`** — Claude-skill frontmatter (`name`, `description`) + 1-page summary of design principles.
- **`preview/`** — ≥15 standalone HTML files. Each ONLY uses `<link rel="stylesheet" href="../tokens.css">` + inline body markup, no JS. Required minimum:
  - `colors-clinical.html`, `colors-action.html`, `colors-semantic.html`
  - `type-display.html`, `type-body.html`, `type-mono.html`
  - `spacing.html`, `radii.html`, `shadows.html`
  - `btn-primary.html`, `btn-secondary.html`, `btn-outline.html`
  - `card.html`, `badge.html`, `input.html`
  - (optional bonuses: `table.html`, `dialog.html`, `tooltip.html`)
- **`ui_kits/web/`** — ≥6 `.tsx` reference layouts (PascalCase): `Header.tsx`, `Sidebar.tsx`, `KpiTile.tsx`, `PatientCard.tsx`, `AppointmentCard.tsx`, `ProcedureRow.tsx`, `EmptyState.tsx`, `BillingSummary.tsx`. Inline styles + token CSS classes; no React imports beyond what's necessary; no Radix here. These are reference layouts demonstrating tokens, not the runtime primitives (D1 builds those).
- **`ui_kits/web/colors_and_type.css`** — copy of root `tokens.css` (mirror chaseglobal's pattern).
- **`data/`** — `patients.js`, `appointments.js`, `invoices.js` — minimal arrays of fixture rows used by the reference layouts.
- **`assets/`** — placeholder `logo.svg`, plus 4–5 SVG icons (e.g., `tooth.svg`, `chart.svg`, `calendar.svg`, `chat.svg`).

## Tests first (`frontend/tests/track_pms_d0/`)

1. **`design-system-files-exist.test.ts`** — uses `node:fs` to assert: `tokens.css`, `README.md`, `SKILL.md` exist; `preview/` has ≥15 `.html` files; `ui_kits/web/` has ≥6 `.tsx` files.

2. **`tokens-css-has-required-variables.test.ts`** — read `tokens.css` as text; regex-assert presence of: `--ds-clinical-500`, `--ds-action-500`, `--color-text-primary`, `--color-action`, `--font-display`, `--text-base`, `--space-4`, `--radius-md`, `--shadow-md`, `--duration-base`. (Don't be over-strict on shade selection — only require representative tokens.)

3. **`preview-pages-import-tokens.test.ts`** — `glob('preview/*.html')`; for each file, assert it contains `tokens.css` reference (via `<link>` or `@import`).

4. **`readme-has-required-headings.test.ts`** — read README.md; assert it contains the headings "Design philosophy", "Color story", "Component principles".

## Implementation guidance

- Use Inter + JetBrains Mono via `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');` at the top of `tokens.css`.
- The dental palette: clinical white (#FAFBFC) + soft greys; action blue around `#0066CC`; success teal around `#0F7A6E`; danger red around `#C72030` (calmer than safety red); warn amber `#F2A73D`. Avoid pure black on white — use `--ds-clinical-900` (e.g. `#0F1722`).
- Reference layouts in `ui_kits/web/*.tsx` should use inline `style={{}}` (matching chaseglobal's inline-style convention) — they are NOT meant to be imported by the live React app (that's D1's job).
- Preview HTML pages should display tokens visually with labels (e.g. a swatch row of all 10 clinical shades, each labelled with its CSS-variable name + hex value).

## Constraints

- Don't touch the live React app. This module is purely the reference repo.
- Don't add a `package.json` at the design-system root — it stays a static folder, mirroring chaseglobal.
- Don't import these files anywhere yet — D1 will hook them into Tailwind.
- All paths under `frontend/design_system/dental-pms.v1/`.

```bash
make test-pms-d0
```
