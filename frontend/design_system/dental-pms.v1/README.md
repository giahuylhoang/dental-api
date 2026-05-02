# dental-pms.v1 — Design System

Single-file, no-build design system for the Dental PMS. Mirrors the flat, token-first conventions of chaseglobal.com.v2.

---

## Design philosophy

The PMS is used by clinicians and front-desk staff across long shifts — often in bright operatory lighting, often under time pressure. Every design decision flows from three constraints:

1. **Glanceable** — critical information (patient name, appointment time, balance owing) must be readable at arm's length in under two seconds.
2. **Forgiving** — destructive actions are never one click away. Confirmations are calm, not alarming.
3. **Calm-confident** — the palette avoids the high-contrast anxiety of safety-red UIs. Danger is communicated clearly but without panic.

The system is intentionally flat: no atoms/molecules/organisms taxonomy, no build step at the design-system layer. One master CSS file (`tokens.css`), PascalCase single-file components, fixture data co-located.

---

## Page templates

The PMS uses four recurring page shapes:

| Template | Description |
|---|---|
| **Dashboard** | KPI tiles across the top, appointment list below, sidebar navigation |
| **Patient record** | Two-column: demographics left, tabbed clinical/billing/comms right |
| **Schedule** | Full-width day/week calendar grid with resource lanes per chair/doctor |
| **List + detail** | Filterable table left, slide-over detail panel right |

All templates share the same sidebar (`Sidebar.tsx`), header bar (`Header.tsx`), and token set. Spacing rhythm is 4px base unit (`--space-1`).

---

## Color story

The palette is built around clinical cleanliness and calm authority.

**Clinical ramp** (`--ds-clinical-*`): Near-white canvas (`#FAFBFC`) through soft blue-greys to near-black (`#0F1722`). Avoids pure `#000000` — the darkest shade still reads as "ink on paper" rather than "screen glare". Used for all text, borders, and backgrounds.

**Action ramp** (`--ds-action-*`): A professional blue centred on `#0066CC`. Familiar, trustworthy, accessible at AA contrast on white. Used for all primary CTAs, links, and focus rings.

**Accent ramp** (`--ds-accent-*`): A calm teal centred on `#0F7A6E`. Communicates success, completion, and positive health outcomes without the harshness of pure green.

**Warn ramp** (`--ds-warn-*`): Warm amber `#F2A73D`. Used for pending states, overdue items, and soft cautions. Never used for errors.

**Danger ramp** (`--ds-danger-*`): A muted red `#C72030` — calmer than safety red, still clearly communicates risk. Used only for destructive actions and critical alerts.

Semantic aliases (`--color-*`) map intent to ramp values. Components always reference semantic tokens, never raw ramp values directly.

---

## Type system

Two typefaces only:

- **Inter** — display and body. Variable-weight, optimised for screen. Loaded via Google Fonts at weights 400/500/600/700.
- **JetBrains Mono** — monospace. Used for procedure codes, invoice numbers, and any data that benefits from fixed-width alignment.

The type scale has 10 steps from `--text-xs` (12px) to `--text-6xl` (60px). Body copy uses `--text-base` (16px) at `--leading-normal` (1.5). Display headings use `--leading-display` (1.1) and `--tracking-tight`.

Six line-height steps (`--leading-tight` through `--leading-display`) and six letter-spacing steps (`--tracking-tighter` through `--tracking-widest`) cover every typographic need without custom one-offs.

---

## Spacing & rhythm

Base unit: **4px** (`--space-1: 0.25rem`).

14 named steps: `--space-1` through `--space-32`. Components use named steps exclusively — no magic numbers. The most common values in the PMS:

- `--space-2` (8px) — tight internal padding (badge, chip)
- `--space-4` (16px) — standard card padding
- `--space-6` (24px) — section gaps
- `--space-8` (32px) — major layout gaps

---

## Component principles

1. **Single-file** — each component is one `.tsx` file. No barrel exports at the design-system layer.
2. **Inline styles + token classes** — components use `style={{ color: 'var(--color-text-primary)' }}` or utility classes that reference tokens. No Tailwind at this layer (D1 wires tokens into Tailwind).
3. **No Radix, no runtime deps** — reference layouts demonstrate token usage only. The live app (D1+) adds accessibility primitives.
4. **Fixture data co-located** — each component that needs data has a `*-data.js` or uses `data/` fixtures. No API calls in reference layouts.
5. **PascalCase filenames** — `PatientCard.tsx`, not `patient-card.tsx`.

---

## Tone of voice

The PMS speaks to professionals, not patients. Copy is:

- **Direct** — "Cancel appointment" not "Would you like to cancel this appointment?"
- **Specific** — "3 overdue invoices" not "Some invoices need attention"
- **Calm** — Error messages explain what happened and what to do next. No exclamation marks in error states.
- **Respectful of time** — Confirmations are one step, not multi-step wizards. Destructive actions require one explicit confirmation, not three.

Labels use sentence case. Navigation items use title case. Button labels use imperative verbs: "Save", "Cancel", "Send reminder".
