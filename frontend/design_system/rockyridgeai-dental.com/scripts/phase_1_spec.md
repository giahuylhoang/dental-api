# Phase 1 — Static-link navigation refactor

## Goal

Convert every cross-page transition in `ui_kits/website/` from React `onClick` into a real `<a href="…html">` link. After this phase the design-system folder must be browsable as a static website where every nav, every CTA, and every "view detail" goes somewhere — even if the destination is a stub page that Phase 2 will flesh out.

## Working directory

`frontend/design_system/rockyridgeai-dental.com/`

All paths below are relative to that directory.

## Read first (do NOT edit)

- `colors_and_type.css` — design tokens (no new ones)
- `SKILL.md`, `README.md` — brand voice + component map
- Existing pages: `ui_kits/website/{index,dashboard,login,patients,schedule,treatment,lab,billing,communications,crm}.html`
- Existing components: `ui_kits/website/{Sidebar,TopBar,Nav,Hero,Pillars,Philosophy,CTA,Footer-or-CTA-merge,LoginCard,KpiTile,PatientCard,AppointmentCard,LabPipeline,ToothChartTile,EmptyState}.jsx`

## Edit list (concrete)

### 1. `ui_kits/website/Sidebar.jsx`
- Define one canonical NAV array of 10 items with these keys (one row each, in this order):
  `dashboard`, `patients`, `schedule`, `plans`, `lab`, `billing`, `comms`, `crm`, `reports`, `settings`.
  Each item: `{ key, label, href, group, iconSvg }`.
  - `key` → see list above
  - `href` → `<key>.html` — **except** `comms` → `communications.html` and `plans` → `plans.html`. (`treatment` is a *patient*-scoped page, so don't expose it as a Sidebar item.)
  - `group` → "Care" for dashboard/patients/schedule/plans/lab; "Operations" for billing/comms/crm; "Insights" for reports; "System" for settings.
- Render each item as a real `<a class="nav-item" href={item.href}>` with `aria-current="page"` when `props.active === item.key`. Keep the existing visual treatment (icon, label, badge dots, collapsed mode).
- Keep the optional `onClick` prop for runtime React-app compatibility — but on the static prototype the `<a href>` is what makes the link work.

### 2. `ui_kits/website/TopBar.jsx`
- Wrap the clinic-name + RR logo cluster in `<a href="dashboard.html">`.
- Add a user-menu trigger that includes a `<a href="login.html?logout=1">Sign out</a>` link (Phase 5 will wire the actual logout, this phase just needs the link to exist).
- The breadcrumb prop continues to be a passthrough string.

### 3. `ui_kits/website/Nav.jsx` (marketing nav, used only by `index.html`)
- "Sign in" link → `href="login.html"`.
- "Schedule a demo" CTA → `href="index.html#contact"` (anchors stay in `index.html`).
- Any other link in the nav: keep its current behavior, but if it's currently `href="#"` and there's no in-page anchor, change it to `href="index.html#<section>"` instead.

### 4. `ui_kits/website/CTA.jsx` (and the inline Footer in CTA.jsx)
- Footer column links: every dead `href="#"` should be either an anchor inside `index.html` or removed. Privacy/Terms can stay as `index.html#legal` for this phase.
- Primary "Book a demo" button stays as a form submit OR becomes `href="index.html#contact"`.

### 5. Each existing app page — swap row clicks to `<a href>`

Inspect every page's `<script type="text/babel">` block and find places where a click handler navigates within the kit. Replace those with a real `<a>` wrapping the row, using the targets below. Keep the visual styling identical — the row is still a clickable card; only the implementation changes.

| File | Click target | href format |
|------|--------------|-------------|
| `dashboard.html` | KPI tiles → page deep links | Today appointments → `schedule.html`; Outstanding balance → `billing.html`; New leads → `crm.html`; Lab pipeline → `lab.html`. Patient cards → `patient-detail.html?id={id}`. |
| `patients.html` | Patient row | `patient-detail.html?id={p.id}` |
| `patients.html` | "View all" links on the side panels | `recalls.html` is NOT in scope — link to `patients.html?filter=recall` instead (same page, query filter) |
| `schedule.html` | Appt block | `appointment-detail.html?id={a.id}` |
| `schedule.html` | Provider names in the side rail | `settings.html#providers` |
| `treatment.html` | Patient-context header avatar | `patient-detail.html?id={p.id}` |
| `treatment.html` | "View all plans" link | `plans.html` |
| `lab.html` | Pipeline card | `lab-case-detail.html?id={c.id}` |
| `lab.html` | Vendor card | `settings.html#vendors` |
| `billing.html` | Invoice row | `invoice-detail.html?id={inv.id}` |
| `billing.html` | Claim row | `invoice-detail.html?id={claim.invoice_id}#claim` |
| `communications.html` | Thread row | `patient-detail.html?id={t.patient.id}#communications` |
| `crm.html` | Lead card | `lead-detail.html?id={lead.id}` |
| `crm.html` | "Create lead" CTA | leave as a button (Phase 2 may add a separate `lead-new.html` — out of scope here) |
| `login.html` | "Forgot password?" | `login.html#forgot` (anchor inside same page; Phase 5 may build a real flow) |

For each row replacement:
- The anchor must NOT change the layout — wrap the existing markup with `<a class="row-link" href={...} style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>` or use a CSS class that already exists.
- Hover/focus states should still work; if a row had `cursor: pointer`, the anchor wrapper inherits that.
- Stop any inline `<button onClick=…>` that was used purely for navigation; they become `<a>` instead.

### 6. Anchor cleanup
- No `<a href="#">` may remain outside `index.html` (which uses `#anchor` for marketing-section scroll).
- Every navigational `<a href="X.html">` in the kit must point to either an existing file OR one of the Phase-2 targets in this allowlist: `reports.html`, `settings.html`, `plans.html`, `patient-detail.html`, `invoice-detail.html`, `appointment-detail.html`, `lead-detail.html`, `lab-case-detail.html`, `denture-case-detail.html`. Other targets are forbidden — pick one of the existing pages or one of these.

## Pass criterion

Run `bash scripts/test_phase1.sh` from this folder. The test must exit 0. It checks:
1. Sidebar.jsx contains all 10 nav keys.
2. Sidebar.jsx renders `<a href>`-style navigation.
3. TopBar.jsx links logo to `dashboard.html` and includes a `login.html` logout link.
4. Nav.jsx links to `login.html`.
5. No stray `href="#"` outside `index.html`.
6. Every `<a href>` target is either real today or in the Phase-2 allowlist.
7. Every existing HTML page returns 200 from a `python3 -m http.server` smoke.

## Rules

- Do NOT add new colours, fonts, sizes, shadows, or radii. Only consume `colors_and_type.css` tokens.
- Do NOT touch `colors_and_type.css`, `README.md`, `SKILL.md`, `preview/*`, `assets/*`, `uploads/*`.
- Do NOT touch any file under `frontend/src/`, `frontend/tailwind.config.js`, the `dental-pms.v1/`, or the `rockyridgeai.com/` folders.
- Do NOT add any new HTML pages in this phase. (Phase 2 does that.)
- Do NOT add JS dependencies via package.json — pages stay browser-only via unpkg + Babel.

## Iteration loop

After each edit, run `bash scripts/test_phase1.sh` and read the output. Fix whatever it flags. Loop until the test exits 0.
