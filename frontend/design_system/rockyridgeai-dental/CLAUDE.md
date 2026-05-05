# CLAUDE.md — Rockyridge Dental AI Design System

These rules apply to any agent (Claude Code, subagents, scripts) working in this design system repo. Read before making changes.

## Design work — invoke the `rockyridge-dental-design` skill first

**Before creating or modifying any UI artifact in this repo, you MUST invoke the `rockyridge-dental-design` skill.** Do not rely on model memory for brand tokens, component patterns, or voice guidelines — the skill (`SKILL.md`) and the full reference (`README.md`) are the single source of truth.

### What counts as "design work"

Any change that touches the visual output of the Rockyridge Dental AI product, including:

- **HTML prototypes** — any page in `preview/`, `ui_kits/website/`, or `_prototype/`
- **CSS tokens** — edits to `colors_and_type.css` or any admin/component stylesheet
- **Components** — JSX/TSX files in `ui_kits/website/` or `components/`
- **Marketing pages** — `index.html`, landing pages, pitch artifacts
- **Data / mock files** — `data/` patient/appointment/invoice seeds and mocks
- **Assets** — SVGs, logos, dental-domain icons

### How to invoke

```
Skill(skill="rockyridge-dental-design")
```

The skill mandates you first read `README.md`, then `colors_and_type.css`, then browse `preview/` for reference components. Honor that sequence — do not skip it.

### Why this rule exists

This design system is the single source of truth for every visual decision in the Rockyridge Dental AI product. It inherits from the parent `rockyridgeai.com` brand but enforces a distinct clinical vocabulary (light-theme default, Navy/Steel/Warm-white palette, Montserrat + Inter typography, sweep-fill buttons, no emoji, definite-article system names). Skipping the skill leads to:

- Introducing new colours, fonts, or radii outside of `colors_and_type.css`
- Using dark theme on clinical surfaces (reserved for login portal only)
- Emoji or filled icons in the UI
- Inconsistent button styles or spacing
- Jargon mismatch ("session" vs "call", "tenant" vs "clinic")

### Key references at a glance

| File | Purpose |
|------|---------|
| `SKILL.md` | Agent-invocable skill manifest |
| `README.md` | Full design system documentation |
| `colors_and_type.css` | Master tokens (shadcn HSL + RR brand + utilities) |
| `preview/*.html` | One self-contained reference page per component |
| `ui_kits/website/` | Full-bleed compositions and prototypes |
