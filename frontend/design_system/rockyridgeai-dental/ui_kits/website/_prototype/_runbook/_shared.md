# Shared context for every Receptionist-prototype task

Every task prompt in `_runbook/` prepends this file. Read it once, treat it as binding.

## Ground truth

- `ui_kits/website/_prototype/INVENTORY.md` — source of truth for routes, verbatim copy, brand voice, kit mechanics, and corrections to the original plan. **Read this first.** If a task contradicts the inventory, the inventory wins.
- `rockyridgeai-dental.com/README.md` — design-system brand voice and tokens.
- `ui_kits/website/_prototype/admin-routing.html` — completed reference page. Mirror its conventions: clinical voice, panel structure, switch / hours-row / save-bar primitives, navy `--rr-navy` save buttons, sticky save bar with dirty-tracking, `<style>` block at top, page-specific CSS scoped via classnames.
- `ui_kits/website/_prototype/AdminSidebar.jsx` — the sidebar component every page must mount as `<AdminSidebar active="<key>" clinicName={CLINIC.name} clinicSlug={CLINIC.slug} />`.
- `ui_kits/website/_prototype/admin-shell.html` — minimal shell + topbar pattern (the `AdminTopBar` stub component you'll inline at the top of each page).

## Brand voice (binding)

- **Clinical, calm, authoritative.** Trusted senior practitioner. Measured, precise.
- **"We → you" framing.** *We* (Rockyridge) build the engine; *you* (the clinic) run your practice on top.
- **No hype words.** Never "AI-powered", "smart", "world-class", "cutting-edge", "seamless", "delight". Replace with concrete specifics.
- **Definite article on system names** in body copy: *The Receptionist. The Call Log. The Greeting. The Schedule.* Capitalised, treated as proper nouns. Nav labels stay bare ("Calls", "Schedule").
- **No emoji.** Anywhere. Toasts, empty states, comments, copy.
- **Casing.** ALL CAPS overlines with 0.15em tracking (`<div class="overline">`). Title Case for CTAs and product statements. Sentence case for descriptive copy.

## Kit mechanics (binding)

- Pages are `.html` files at `ui_kits/website/_prototype/`. Self-contained — no bundler, no build step.
- Stylesheet: `<link rel="stylesheet" href="../../../colors_and_type.css">` brings in tokens (`--rr-navy`, `--rr-warm-white`, `--rr-parchment`, `var(--font-display|ui|mono)`, `hsl(var(--primary))`, `hsl(var(--ring))`, etc.). Don't redefine these.
- React + ReactDOM + Babel via UMD CDN (see `admin-routing.html` head).
- Page-specific CSS lives in an inline `<style>` block at the top of the page.
- Mock: `<script src="../../../data/admin_mock.js"></script>` exposes `window.ADMIN_MOCK` (read-only — Task 3B is the only task allowed to expand it).
- Helper: `<script src="../../../lib/query.js"></script>`. Top of the page: `window.RRD?.requireSession?.();`.
- Sidebar: `<script type="text/babel" src="AdminSidebar.jsx"></script>`.
- Mount root: `<div id="root"></div>` then `ReactDOM.createRoot(document.getElementById('root')).render(<Body />);`.
- Use `React.useState` (no destructured hooks — UMD doesn't expose them as bare names).

## Forbidden files (never edit)

- `ui_kits/website/login.html`
- `ui_kits/website/Sidebar.jsx`
- Any existing kit page (`dashboard.html`, `patients.html`, `schedule.html`, `settings.html`, `lab.html`, etc.)
- Any existing `.jsx` component at `ui_kits/website/<Name>.jsx` (TopBar, KpiTile, DataTable, EmptyState, Drawer, etc.) — read for reference only.
- Anything outside `rockyridgeai-dental.com/`.

If you need a primitive that doesn't exist yet, prefer **inline JSX inside the page** (mirroring how `admin-routing.html` defines `Switch` and `HoursRow` inline). Only extract to a new `.jsx` file if the same component is used by 3+ pages.

## Verbatim copy contract

When the task says "verbatim", that string must appear in the rendered DOM exactly as written. Do not paraphrase. Common verbatim strings the prototype owes the user:
- "Recent calls and transcripts."
- "CRM rollup from agent calls."
- "Today's appointments (read-only)."
- "Hours, holidays, transfer rules."
- "Edit the AI greeting message."
- "AI SIP URI (read-only here; engineer-managed)"
- "Both blank means closed that day."
- "What would the agent do at a given moment, against the *currently saved* rules? (Save first if you want to preview a draft.)"
- "Welcome to … How can I help you today?" (`…` is U+2026)
- "No custom greeting persisted yet. The agent uses the YAML default until you save one."
- "First-time edits land as `pending_review`. An engineer (email allow-listed in `GREETING_APPROVERS`) must call `/approve` once per clinic; after that, edits auto-approve."
- "Approve clinic (engineer-gated)"

## Smoke test contract

After writing files, run from the `rockyridgeai-dental.com/` repo root:

```
node -e "console.log(require('fs').readFileSync('<output-file>', 'utf-8'))" | grep -F "<verbatim-required-1>" >/dev/null && echo OK1
node -e "console.log(require('fs').readFileSync('<output-file>', 'utf-8'))" | grep -F "<verbatim-required-2>" >/dev/null && echo OK2
```

(or equivalent. The point: every verbatim string the task lists must be present in the file.)

If you cannot satisfy a success criterion, **stop and write a `_runbook/_state/<task-id>.failed.md` file** describing what failed and why — do not silently produce partial output.

## Output contract

Write a single `<file>` per task as specified. Do not modify any other file. After success, write `_runbook/_state/<task-id>.done.md` with: list of files written, file sizes, and a paragraph on what's still missing for the user to verify visually.
