---
name: rockyridge-dental-design
description: Use this skill to generate well-branded interfaces, components, and assets for Rockyridge Dental AI — the dental practice management product of Rockyridge AI Solutions. Provides shadcn-shape primitives layered with the parent Rockyridge brand language (Navy / Steel / Warm-white palette, Montserrat + Inter typography, sweep-fill button motif). Default light theme for clinical surfaces; dark theme reserved for the login portal. Use for production runtime code, throwaway HTML prototypes, marketing pages, and dental-domain composites (patient cards, tooth charts, lab pipelines, treatment plans).
user-invocable: true
---

## When to invoke

- Implementing or styling any UI inside the Rockyridge Dental AI app (`frontend/src/` of the dental-api repo).
- Generating a static HTML prototype, marketing page, or pitch artifact for the dental product.
- Adding a new shadcn-shape component and needing the brand-correct token bindings.
- Designing a dental-domain composite (PatientCard, AppointmentCard, ToothChart, LabPipeline, KpiTile, etc.).
- Resolving a design ambiguity ("what colour is the focus ring?", "which font for KPI numbers?", "is this card the right radius?").

## How to use

1. **Read `README.md` first.** It documents brand voice, component library, file layout, and the design lineage (shadcn → RR brand, in that order).
2. **Read `colors_and_type.css`.** Every token is here. If a value isn't tokenised, use the closest existing one — do *not* invent new colours, radii, or font sizes.
3. **Browse `preview/` for the component you need.** Each preview is a self-contained HTML page that imports `../colors_and_type.css` and demonstrates the component in default + variant states. Copy the markup as a starting point.
4. **Check `ui_kits/website/` for full-bleed compositions.** PascalCase JSX files mirror the parent `rockyridgeai.com/ui_kits/website/` layout. `dashboard.html` (light) and `login.html` (dark) are the canonical product prototypes.
5. **Output rules:**
   - For *production code* (live React app), import the runtime primitives at `frontend/src/components/ui/<name>.tsx` — they already consume these tokens. Do not reach into the design_system folder for runtime imports.
   - For *throwaway artifacts* (HTML mocks, slides, pitch decks), copy the relevant preview as a starting point, swap the `../colors_and_type.css` link to a relative path that resolves, and stay strict to the token names.
6. **Brand voice:** authoritative, clinical, calm. Never emoji. "We → you" framing. Definite article on system parts (*The Schedule*, *The Roster*, *The Lab*).

## What NOT to do

- Do not introduce new colours, fonts, or shadows outside `colors_and_type.css`.
- Do not flip to dark theme for clinical surfaces. Login portal is the only dark-theme exception.
- Do not use emoji. Do not use filled icons. Do not use playful / spring easing.
- Do not bypass `--primary` / `--foreground` / `--border` in favour of raw hex values inside components — keep the indirection so the dark theme works.

If invoked without specific guidance, ask the user what they're trying to build (marketing page? clinical screen? component variant?), then act as an expert designer outputting either HTML prototypes or production React code.
