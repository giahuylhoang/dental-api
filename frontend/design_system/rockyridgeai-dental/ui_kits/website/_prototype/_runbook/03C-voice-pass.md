# Task 3C — Voice & empty-state pass

One sweep over every prototype page enforcing the kit's clinical voice and reassuring empty states.

## Output

Edits across these files:
- `ui_kits/website/_prototype/admin-dashboard.html`
- `ui_kits/website/_prototype/admin-calls.html`
- `ui_kits/website/_prototype/admin-call-detail.html`
- `ui_kits/website/_prototype/admin-patients.html`
- `ui_kits/website/_prototype/admin-schedule.html`
- `ui_kits/website/_prototype/admin-routing.html`
- `ui_kits/website/_prototype/admin-greeting.html`

Do not modify `data/admin_mock.js`, `AdminSidebar.jsx`, or any non-admin file.

## Voice rules (binding — see `_shared.md` for the full set)

- **Replace** any instance of these jargon words **outside the engineer view**: `session` → `call`, `tenant` → `clinic`, `endpoint` → kept only inside the right-rail engineer view; remove anywhere else. `latency` is OK in the engineer view; outside, prefer "response time".
- **No hype words** anywhere: never `AI-powered`, `smart`, `world-class`, `cutting-edge`, `seamless`, `delight`, `revolutionary`, `unleash`, `supercharge`. If found, replace with a concrete specific.
- **No emoji** anywhere — strip any U+1F000–U+1FFFF range characters and common ones (`✓`, `✔`, `→` is OK as it's a structural arrow, not decorative).
- **Definite-article system names** in body copy: ensure each page uses one of *The Receptionist · The Call Log · The Roster · The Schedule · The Greeting · Routing* in its sub-paragraph. Sidebar nav labels stay bare (`Calls`, `Patients`, etc.).
- **Save buttons** are confident, not tentative: "Save routing" not "Submit form".

## Empty-state copy

Every empty state must have a reassuring one-liner. Verify (and fix if missing):

- `admin-dashboard.html` — when zero calls in mock: `The first call your AI takes will land here. Nothing to set up.`
- `admin-calls.html` — when filters yield zero: `No calls match these filters. Widen the date range or clear an outcome to see more.`; when mock is empty: `No calls yet. The first call we take for you will land here.`
- `admin-call-detail.html` — when transcript empty: `This call ended before either side spoke. The audio above is the full record.`; when call_id not found: `Call not found.` + back-link.
- `admin-patients.html` — when zero patients: `Your patient list builds itself as we take calls. Once a few come in, you'll see them here, with every conversation linked.`; when filters yield zero: `No patients match. Try clearing a filter.`
- `admin-schedule.html` — when zero appointments today: `Nothing on the books for this day.`
- `admin-greeting.html` — when no record: `No custom greeting persisted yet. The agent uses the YAML default until you save one.` (verbatim from source)
- `admin-routing.html` — preview unset: `Pick a moment and press Preview to see what the agent would do.`

If an empty state's copy is missing or wrong, fix only that string. If it's already correct, leave it.

## Helper-text rule

Every helper text under a form field should start with a verb the user does, not the system. Example: "Add days you're closed beyond regular hours." (correct) vs. "Holidays are days when the AI..." (wrong — system-first). Sweep all helpers in `admin-routing.html` and `admin-greeting.html`.

## Tooltip rule

Tooltips on engineer-only / read-only fields explain *who* changes the field, not *how*. The "AI SIP URI" tooltip in routing is the model: `Your engineering partner sets this up. You can copy it; only they can change it.`

## Forbidden

- Do not refactor layout, change classnames, or restructure JSX. This is a copy-only pass.
- Do not change the verbatim copy strings already locked in (`Welcome to … How can I help you today?`, `Both blank means closed that day.`, `AI SIP URI (read-only here; engineer-managed)`, etc.). If you find them already present, leave them.
- Do not delete entire sections — only individual strings.

## Success criteria

- Grep across all 7 admin-* pages turns up zero hits for `AI-powered`, `world-class`, `cutting-edge`, `seamless`, `delight`, `revolutionary`, `supercharge`, `unleash`, `session`, `tenant`, `smart`. (`session` and `tenant` are OK inside an engineer-view section — qualify the grep with negation if needed.)
- Every empty-state string above is present in its page (grep test).
- Every helper text starts with a verb (manual sweep).
- Write `_runbook/_state/03C.done.md` listing every replacement made (find → replace → file:line).
