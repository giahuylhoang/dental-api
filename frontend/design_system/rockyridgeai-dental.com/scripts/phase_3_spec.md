# Phase 3 — Shared component extraction

## Goal

Extract repeated patterns from the 19 existing HTML pages into 15 PascalCase JSX components in `ui_kits/website/`. Each component is a single-file React function that registers itself on `window.<Name>`. Pages must then `<script src="<Name>.jsx" type="text/babel">` and use `<Name>` in their JSX.

## Working directory

`frontend/design_system/rockyridgeai-dental.com/`

## Components to create (each `ui_kits/website/<Name>.jsx`)

| File | Purpose |
|------|---------|
| `StatusPill.jsx` | Single source of truth for ALL status enums. Props: `kind` (one of: lead, claim, invoice, appointment, lab_case, denture_case, treatment_plan, patient_lifecycle, recall, generic), `value` (canonical enum string). Internally maps `kind+value` → tone (default | success | warn | danger | info | muted) → existing token swatches. Must cover EVERY canonical spelling listed below. |
| `DataTable.jsx` | Props: `columns` array `[{key, label, align, render?, mono?, width?}]`, `rows` array, `onRowHref?` (function row → href so the row becomes an `<a>`), `empty?` (EmptyState child). Renders the kit's standard table style. |
| `Drawer.jsx` | Right-side slide-over panel. Props: `open`, `onClose`, `title`, `width?`, `children`. Lock body scroll; backdrop click closes. |
| `Tabs.jsx` | Horizontal tab strip. Props: `tabs` (array `[{key, label, count?}]`), `active`, `onChange`. Active tab gets navy underline. |
| `FormField.jsx` | Labelled input wrapper. Props: `label`, `hint?`, `error?`, `children` (the input). Label uses Inter 500 12px uppercase. |
| `Breadcrumb.jsx` | Props: `items` array `[{label, href?}]`. Last item is bolded + not linked. |
| `MoneyCell.jsx` | Wraps `Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' })`. Prop: `amount` (number) and optional `negative` flag (renders in red). Mono font. |
| `MonoText.jsx` | Tiny wrapper that renders children in JetBrains Mono with `letter-spacing: 0.02em`. Useful for IDs, timestamps, dates. |
| `IconButton.jsx` | Square 32px button with an SVG child. Props: `label` (a11y), `onClick?`, `href?`, `variant?` (ghost | primary). |
| `SearchInput.jsx` | Search field with embedded magnifier icon. Props: `value`, `onChange`, `placeholder?`. |
| `FilterChips.jsx` | Pill-row filter. Props: `chips` (array `[{key, label, count?}]`), `active`, `onChange`. |
| `KanbanBoard.jsx` | Generalize `LabPipeline.jsx`. Props: `columns` (array `[{key, label, dot?}]`), `cards` (array), `getColumn` (card→column key), `renderCard` (card → JSX), `onCardHref?` (card → href). |
| `CalendarGrid.jsx` | Generalize the schedule day grid. Props: `slotMinutes` (default 30), `dayStartHour`, `dayEndHour`, `columns` (array `[{key, label}]`), `events` (each event has `start, end, columnKey, color, render`), `nowMinutes?` (renders the red "now" line). |
| `Avatar.jsx` | 3-letter monogram circle. Props: `name`, `size?` (default 36), `seed?` (string used for deterministic color), `href?` (wraps in <a>). |
| `ChartCard.jsx` | KPI card with title + big number + optional sparkline (inline SVG generator). Props: `title`, `value`, `delta?`, `trend?` (array of numbers → sparkline), `unit?`. |

## Refactor existing pages

For each existing page, replace inline patterns with the new components.

- **Status pills**: every `<span class="pill">…</span>` (or inline `style={{background, color}}` pill) should become `<StatusPill kind=… value=…>`. Pages that need this: `patients`, `schedule`, `treatment`, `lab`, `billing`, `communications`, `crm`, `plans`, `lab-case-detail`, `lead-detail`, `appointment-detail`, `invoice-detail`, `denture-case-detail`.
- **Tables**: The recent-patients/invoices/leads tables already share columns/spacing → use `DataTable`.
- **Tabs**: `treatment.html`, `patient-detail.html`, `lead-detail.html`, `settings.html` → use `Tabs`.
- **Drawers**: any inline drawer markup in the existing 10 pages → wrap with `Drawer`.
- **Forms**: every label+input pair → wrap with `FormField`.
- **Money**: every CAD currency render → `<MoneyCell amount={n}>`.
- **Mono ids/timestamps**: every JetBrains-mono inline span → `<MonoText>{…}</MonoText>` (only for substantial usages; tiny one-off mono spans can stay).
- **Avatars**: every monogram circle → `<Avatar name={…}>`.
- **Search inputs / filter chips**: replace inline `<input search>` and pill row pattern.
- **Kanban**: `lab.html` and `crm.html` → use `KanbanBoard` (delete the inline columns implementation, but keep `LabPipeline.jsx` as a thin adapter that wraps `KanbanBoard` so external imports still work).
- **Schedule**: `schedule.html` → use `CalendarGrid` (delete the inline absolute-positioning math).

## Canonical status spellings (StatusPill must support these exactly)

- Lead: `NEW | CONTACTED | QUALIFIED | CONVERTED | LOST`
- Claim: `draft | submitted | accepted | adjudicated | paid | rejected | partial`
- Invoice: `draft | issued | partial | paid | void`  (also `overdue` for filter)
- Appointment: `SCHEDULED | CONFIRMED | COMPLETED | NO_SHOW | PENDING | PENDING_SYNC | RESCHEDULED | REMINDER_SENT | CANCELLED`
- LabCase: `draft | sent | in_progress | returned | remake | cancelled`
- DentureCase: `open | closed`
- TreatmentPlan: `draft | presented | accepted | in_progress | completed | declined`
- PatientLifecycle: `pending | active | inactive | deceased | merged`
- Recall: `pending | sent | completed | cancelled`
- Generic: any string is rendered with the muted tone — fallback only.

## Tone palette (use existing tokens — do not add new ones)

- success: `#2A7D4F` text on `#E8F5EE` bg (or the existing `--success-*` tokens if defined in `colors_and_type.css`)
- warn: `#B45309` text on `#FDF3E5` bg
- danger: `#9B2335` text on `#F8E5E8` bg
- info: `#2E6494` text on `#D9EAF5` bg (or steel-bg tokens)
- muted: `#4A5568` text on `#F5F2EC` bg

(If exact tokens already exist in `colors_and_type.css`, use those instead of raw hex.)

## Pass criterion

Run `bash scripts/test_phase3.sh`. It checks:
1. Every component file exists and is non-empty.
2. Every component file exposes `window.<Name>`.
3. `<StatusPill>` is referenced by ≥ 4 pages.
4. Each component is loaded by at least one HTML page (`<script src="<Name>.jsx">`).

## Rules

- Same brand rules as prior phases — no new colours/fonts/sizes/shadows.
- Each component file is self-contained (one function + the window registration). No external runtime deps.
- Keep visual identity: refactored pages must look indistinguishable to the eye from before. If a refactor would change pixel layout, leave the inline version alone for that one usage and document why in a single-line comment in the page.
