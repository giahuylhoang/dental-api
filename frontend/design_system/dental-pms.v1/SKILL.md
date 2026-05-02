---
name: dental-pms-v1-design-system
description: >
  Design system tokens, reference layouts, and preview pages for the Dental PMS.
  Single-file, no-build. Mirrors chaseglobal.com.v2 conventions.
  Consumed by D1 (Tailwind token wiring) and downstream feature tracks.
---

# dental-pms.v1 Design System — Skill Summary

## What this is

A static reference repository containing:
- `tokens.css` — all CSS custom properties (colors, type, spacing, radii, shadows, motion)
- `preview/` — standalone HTML pages demonstrating each token group visually
- `ui_kits/web/` — PascalCase TSX reference layouts showing token usage in context
- `data/` — fixture arrays for patients, appointments, invoices
- `assets/` — logo and icon SVGs

## Core design principles

**Clinical clean** — near-white canvas, soft grey ramps, no pure black. Designed for bright clinical environments.

**Calm-confident** — action blue (#0066CC) for CTAs, teal (#0F7A6E) for success, muted red (#C72030) for danger. Avoids anxiety-inducing high contrast.

**Glanceable** — information hierarchy is strict: patient name > appointment time > status > detail. KPI tiles surface the most important numbers at a glance.

**Forgiving** — destructive actions require explicit confirmation. No one-click deletes.

## Token conventions

- All tokens live in `:root` in `tokens.css`
- Color base tokens: `--ds-{ramp}-{shade}` (e.g. `--ds-action-500`)
- Semantic tokens: `--color-{intent}` (e.g. `--color-action`, `--color-danger`)
- Typography: `--font-{family}`, `--text-{size}`, `--leading-{name}`, `--tracking-{name}`
- Spacing: `--space-{step}` (4px base unit)
- Radii: `--radius-{size}`
- Shadows: `--shadow-{size}`
- Motion: `--ease-{curve}`, `--duration-{speed}`

## Usage by downstream tracks

- **D1** — imports `tokens.css` path into Tailwind config as CSS variable source
- **D2+** — React components reference `--color-*` and `--space-*` via inline styles or Tailwind classes
- **Preview pages** — standalone HTML, no JS, link only to `tokens.css`
