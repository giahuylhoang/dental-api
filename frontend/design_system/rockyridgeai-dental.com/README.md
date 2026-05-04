# Rockyridge Dental AI — Design System

## Overview

**Rockyridge Dental AI** is a vertical product of **Rockyridge AI Solutions** — a sovereign clinical platform for denturists, dentists, and dental clinic operators. The brand inherits Rockyridge AI's *Systems Thinking* philosophy and visual language, then layers a clinical UI vocabulary on top: shadcn/ui-shape primitives, calm light-theme surfaces, and dental-domain composites (tooth charts, lab pipelines, treatment plans, recall workflows).

This design system is the single source of truth for every visual decision in the product. It is a sibling of `rockyridgeai.com/` and was written so that anyone — designer, engineer, or AI agent — can produce on-brand UI without re-litigating type, colour, or spacing.

### Design lineage

| Layer | Source | What it contributes |
|------|--------|---------------------|
| Brand | `rockyridgeai.com/` | Navy / Steel / Warm-white palette · Montserrat + Inter typography · sweep-fill button motif · "we → you" voice |
| Component shape | [shadcn/ui](https://ui.shadcn.com) | HSL token shape · semantic naming (`--background`, `--foreground`, `--primary`, `--muted`, …) · Radix primitives mental model |
| Domain | Rockyridge Dental AI | Patient · Provider · Schedule · Lab · Treatment Plan · Insurance composites |

We start from shadcn's component vocabulary and layer the Rockyridge brand on top — *not* the reverse. That ordering matters: it means every shadcn component drops into our codebase against `colors_and_type.css` and inherits the brand without bespoke styling.

---

## Brand wordmark

| Element | Treatment |
|---------|-----------|
| Mark    | `RR` lettermark — `assets/RR_logo_blue.svg` (light bg) · `assets/RR_logo_white.svg` (dark bg) |
| Brand line | **ROCKYRIDGE** · Montserrat 800 · 0.08em tracking · uppercase |
| Sub line   | **DENTAL AI** · Montserrat 400 · 2.1px tracking · uppercase |

The wordmark is locked to the mark with 12px gap. Never recolour, distort, add a glow, or place on a busy photo. Reference: `preview/logo.html`, `.rr-wordmark` utility in `colors_and_type.css`.

The parent brand uses `ROCKYRIDGE / AI SOLUTIONS`. The dental product corrects to `ROCKYRIDGE / DENTAL AI` — same display family, same lockup geometry, only the sub line changes.

---

## CONTENT FUNDAMENTALS

### Tone & voice
- **Authoritative, calm, clinical.** The product speaks like a trusted senior practitioner — measured, precise, never breathless. Borrowed directly from the parent brand and sharpened for healthcare context.
- **"We → you" framing.** *We* (Rockyridge) build the engine; *you* (the clinic) run your practice on top of it.
- **No hype.** Never "world-class," "cutting-edge," "AI-powered." Always specific: "schedules 240 patients/day with no double-booking," "exports CSV to PMS," "OHIP code 23311 lookup."
- **Definite article on system names.** *The Schedule. The Roster. The Lab.* — system parts are named, capitalised, treated as proper nouns.

### Casing
- Section labels / overlines: `ALL CAPS · 0.15EM TRACKING`
- Section headlines: Title Case for product statements, sentence case for descriptive copy
- CTAs: Title Case (e.g., "Schedule a Demo", "Open Patient Chart")
- Body: sentence case

### Emoji usage
**None.** Not in the marketing site, not in the app, not in toasts or empty states. The product does not use emoji.

### Copy examples
- ✅ *"Architecting Sovereign Clinical Systems."*
- ✅ *"Your patient roster is either a liability or a competitive edge."*
- ✅ *"Open the chart. The history is already there."*
- ❌ *"AI-powered scheduling for the modern dentist!"*
- ❌ *"Welcome back :) Let's get you scheduled today."*

---

## VISUAL FOUNDATIONS

### Theme strategy
- **Light theme is the default** for every clinical / admin / patient-facing surface. Operators look at this UI for 8+ hours; warm-white reduces eye strain.
- **Dark theme is reserved** for the **login portal** and any marketing hero pulled from the parent rockyridgeai.com aesthetic. Triggered by adding `.dark` to `<html>` or `<body>`. Component primitives auto-adapt because every colour resolves through `hsl(var(--…))`.
- We do **not** offer a user-facing theme toggle inside the app. The chart and the schedule are clinical instruments — predictable surface colour matters more than personalisation.

### Colour
- **Primary** — Steel Blue `#3A7FBD`. Single action colour. CTAs, links, focus rings, primary chart series.
- **Secondary / Brand** — Navy `#0A192F`. Used for the sidebar, login portal, and marketing hero. Authority colour.
- **Surface** — Warm White `#FAF9F6` (page) · `#FFFFFF` (cards) · Off-White `#F5F2EC` (subtle wash). No greys-on-greys.
- **Ink** — `#1C2333` body · `#3D4D61` secondary · `#4A5568` muted.
- **Semantic** — Success `#2A7D4F` · Warning `#B45309` · Error `#9B2335` · Info = Steel.

Dark sections use `#060F1E` / `#0A192F` with warm-white text. Never grey or pure-black backgrounds.

### Typography
- **Display** — `Montserrat` 600/700/800/900. Headlines, hero, big numbers, KPI tiles. Tight tracking on display sizes (`-0.03em`).
- **UI / Body** — `Inter` 300/400/500/600/700. Every label, button, body paragraph, table cell, form field.
- **Mono** — `JetBrains Mono` 400/500/600. Patient IDs, tooth numbers, lot numbers, codes, durations. Anything that must be a fixed-width clinical reference.

The parent rockyridgeai.com README mentions Playfair + Lora as the *aspirational* serif set; in practice the live site renders with Montserrat + Inter. The dental sub-brand standardises on the live set so engineering has a single typography contract to ship.

### Spacing & layout
- Generous whitespace. Section vertical padding never less than `64px` desktop / `40px` mobile.
- Max content width `1200px`. Text columns capped at `68ch`.
- Grid: 12-column, `24px` gutters. Three-pillar / three-KPI layouts always equal thirds.
- Sidebar fixed left (240px expanded / 64px icon-only). Top bar fixed top (`64px`). No fixed right rail.

### Motion
- `250ms` ease-out for hover / state changes; `400ms` ease-out for page-level reveals.
- Fade + 16px upward drift for section entry.
- Sweep-fill button: `320ms` ease-out, X translate `-101% → 0`.
- No bouncy / spring / playful easing. No spinning loaders — use `Skeleton` for indeterminate state.

### Component shape
- Default border radius `6px`. Pills `999px`. Sharp section blocks `0`. Avoid the over-rounded "consumer-app" feel.
- Card: white bg, `1px solid var(--rr-parchment)`, `shadow-sm` default, `shadow-md` on hover. `32px` padding desktop.
- Inputs: white bg, `1.5px solid var(--rr-mist)`, focus → `1.5px steel-500` + `3px steel-100` ring.
- Shadows are navy-tinted, never pure black (`rgba(10,25,47,…)`).

### Iconography
- **Lucide Icons** only — `stroke-width: 1.5`, `currentColor` fill. Never filled icons. Never emoji.
- Sizes: `16px` inline · `20px` UI · `24px` feature · `32–48px` hero / pillar.
- Dental-domain icons commonly used: `tooth` (custom SVG, in `assets/`), `calendar`, `clipboard-list`, `flask-conical` (lab), `file-text` (chart), `dollar-sign`, `users`.

### Sweep-fill button (signature interaction)
The hallmark RR interaction. Default state: transparent fill, 1.5px `currentColor` border. Hover: `::before` pseudo-element sweeps from `translateX(-101%)` to `0` filling with the accent colour while text flips to `--primary-foreground`. Always 320ms ease-out. Implemented in `colors_and_type.css` under `.btn` + variants (`.btn-primary`, `.btn-navy`, `.btn-white`, `.btn-ghost`, `.btn-destructive`, `.btn-solid`).

---

## COMPONENT LIBRARY

The system covers the full shadcn/ui surface area, organised by purpose. Each line lists the preview file + the runtime file (in the live React app under `frontend/src/components/ui/`).

### 1. Data display
| Component   | Preview                                    | Runtime |
|-------------|--------------------------------------------|---------|
| Accordion   | `preview/accordion.html`                   | `accordion.tsx` |
| Avatar      | `preview/avatar.html`                      | `avatar.tsx` |
| Badge       | `preview/badge.html`                       | `badge.tsx` |
| Card        | `preview/card.html`                        | `card.tsx` |
| Carousel    | `preview/carousel.html`                    | `carousel.tsx` |
| Chart       | `preview/chart.html`                       | `chart.tsx` |
| Separator   | `preview/separator.html`                   | `separator.tsx` |
| Skeleton    | `preview/skeleton.html`                    | `skeleton.tsx` |
| Table       | `preview/table.html`                       | `table.tsx` |
| Tooltip     | `preview/tooltip.html`                     | `tooltip.tsx` |

### 2. Forms & inputs
| Component   | Preview                | Runtime |
|-------------|------------------------|---------|
| Button      | `preview/button.html`  | `button.tsx` |
| Checkbox    | `preview/checkbox.html`| `checkbox.tsx` |
| Combobox    | `preview/combobox.html`| `combobox.tsx` |
| Date Picker | `preview/date-picker.html` | `date-picker.tsx` |
| Form        | `preview/form.html`    | `form.tsx` |
| Input       | `preview/input.html`   | `input.tsx` |
| Input OTP   | `preview/input-otp.html` | `input-otp.tsx` |
| Label       | `preview/label.html`   | `label.tsx` |
| Radio Group | `preview/radio-group.html` | `radio-group.tsx` |
| Select      | `preview/select.html`  | `select.tsx` |
| Slider      | `preview/slider.html`  | `slider.tsx` |
| Switch      | `preview/switch.html`  | `switch.tsx` |
| Textarea    | `preview/textarea.html`| `textarea.tsx` |
| Toggle      | `preview/toggle.html`  | `toggle.tsx` |

### 3. Feedback & overlays
| Component    | Preview                  | Runtime |
|--------------|--------------------------|---------|
| Alert        | `preview/alert.html`     | `alert.tsx` |
| Alert Dialog | `preview/alert-dialog.html` | `alert-dialog.tsx` |
| Dialog       | `preview/dialog.html`    | `dialog.tsx` |
| Drawer       | `preview/drawer.html`    | `drawer.tsx` |
| Hover Card   | `preview/hover-card.html`| `hover-card.tsx` |
| Popover      | `preview/popover.html`   | `popover.tsx` |
| Progress     | `preview/progress.html`  | `progress.tsx` |
| Sheet        | `preview/sheet.html`     | `sheet.tsx` |
| Sonner       | `preview/sonner.html`    | `sonner.tsx` |

### 4. Navigation
| Component       | Preview                    | Runtime |
|-----------------|----------------------------|---------|
| Breadcrumb      | `preview/breadcrumb.html`  | `breadcrumb.tsx` |
| Context Menu    | `preview/context-menu.html`| `context-menu.tsx` |
| Dropdown Menu   | `preview/dropdown-menu.html` | `dropdown-menu.tsx` |
| Menubar         | `preview/menubar.html`     | `menubar.tsx` |
| Navigation Menu | `preview/navigation-menu.html` | `navigation-menu.tsx` |
| Pagination      | `preview/pagination.html`  | `pagination.tsx` |
| Tabs            | `preview/tabs.html`        | `tabs.tsx` |

### 5. Layout & utilities
| Component    | Preview                  | Runtime |
|--------------|--------------------------|---------|
| Aspect Ratio | `preview/aspect-ratio.html` | `aspect-ratio.tsx` |
| Collapsible  | `preview/collapsible.html`  | `collapsible.tsx` |
| Command      | `preview/command.html`      | `command.tsx` |
| Resizable    | `preview/resizable.html`    | `resizable.tsx` |
| Scroll Area  | `preview/scroll-area.html`  | `scroll-area.tsx` |
| Sidebar      | `preview/sidebar.html`      | `sidebar.tsx` |
| Typography   | `preview/typography.html`   | n/a (semantic) |

### Foundation tokens (also in `preview/`)
`colors-navy.html` · `colors-steel.html` · `colors-neutral.html` · `colors-semantic.html` · `colors-chart.html` · `type-display.html` · `type-body.html` · `type-scale.html` · `type-mono.html` · `spacing.html` · `radii.html` · `shadows.html` · `motion.html` · `logo.html` · `overline.html` · `blockquote.html`

---

## FILE INDEX

```
README.md                    ← This file
SKILL.md                     ← Agent-invocable skill manifest
colors_and_type.css          ← Master tokens (shadcn HSL + RR brand + utilities)

assets/
  RR_logo_blue.svg           ← Navy lettermark — light bg
  RR_logo_white.svg          ← White lettermark — dark bg
  tooth.svg                  ← Dental glyph (custom)
  …                          ← Other dental icons (built as needed)

uploads/
  RR_logo_blue.svg
  RR_logo_white.svg

preview/
  *.html                     ← One self-contained reference page per component / token

ui_kits/
  website/
    README.md                ← Kit notes
    index.html               ← Marketing prototype
    dashboard.html           ← Light-theme PMS dashboard prototype
    login.html               ← Dark-theme login portal prototype
    Nav.jsx                  ← Top navigation
    Hero.jsx                 ← Marketing hero (animated node graph)
    Sidebar.jsx              ← App shell sidebar
    TopBar.jsx               ← App shell top bar
    KpiTile.jsx              ← Dashboard KPI tile
    PatientCard.jsx          ← Patient summary card
    AppointmentCard.jsx      ← Appointment list item
    LabPipeline.jsx          ← Lab Kanban column
    ToothChartTile.jsx       ← Compact dental chart
    LoginCard.jsx            ← Dark-theme login form
    EmptyState.jsx           ← Standard empty state
    Footer.jsx               ← Marketing footer

data/
  patients.js                ← Demo seed
  appointments.js
  invoices.js
```

---

## Versioning & change log

This system is `v1`. Token changes and shape changes happen in lockstep with the runtime React app. Breaking changes bump the major; cosmetic fixes bump the minor.

The runtime app consumes tokens via:
```css
/* frontend/src/index.css */
@import '../design_system/rockyridgeai-dental.com/colors_and_type.css';
```

…and Tailwind extends from the same HSL channels in `tailwind.config.js`.
