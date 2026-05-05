# Task 3A — INDEX integration & navigation sanity

Wire the AI Receptionist prototype into the kit's discovery surface. Verify every page shares chrome and links.

## Output

Two file changes:

1. **Modify** `ui_kits/website/INDEX.md` — append a new top-level section `## AI Receptionist Admin Prototype` (place it directly under the existing `## Pages` table, before `---`). The section lists every prototype artifact with one-line descriptions, in this order:

   ```
   ## AI Receptionist Admin Prototype

   The Receptionist is the AI voice agent that handles calls when the front desk can't. The pages below are a parallel light-theme prototype scoped to the receptionist admin — they coexist with the PMS pages above, share the same tokens, but use a separate `AdminSidebar`.

   | File | Purpose | Sidebar Key |
   |------|---------|-------------|
   | `_prototype/admin-shell.html`         | Shell preview — sidebar + topbar + main slot              | dashboard |
   | `_prototype/admin-dashboard.html`     | The Receptionist overview — ROI tiles, trend, quick links | dashboard |
   | `_prototype/admin-calls.html`         | The Call Log — filtered list with audio previews          | calls |
   | `_prototype/admin-call-detail.html`   | Single call — transcript, audio, engineer view           | calls |
   | `_prototype/admin-patients.html`      | The Roster — CRM rollup with drill-in drawer              | patients |
   | `_prototype/admin-schedule.html`      | The Schedule — read-only day view, AI vs. front-desk      | schedule |
   | `_prototype/admin-routing.html`       | Routing — hours, holidays, transfer rules, simulator     | routing |
   | `_prototype/admin-greeting.html`      | Greeting — editable agent greeting + engineer approval    | greeting |

   ### Components (admin-only)

   | File | Purpose |
   |------|---------|
   | `_prototype/AdminSidebar.jsx` | Navy sidebar scoped to the receptionist admin |

   ### Data

   - `data/admin_mock.js` — `window.ADMIN_MOCK` with clinic identity, routing, greeting, KPIs, calls, transcripts, patients, appointments. Single source for all admin pages.
   ```

2. **Verify (do not modify)** that every admin-* prototype page already mounts `<AdminSidebar active="<key>" ...>` with the correct active key (matches the sidebar key column above). If any page has a wrong or missing active key, **fix only that line** in the offending page — do not edit anything else.

## Forbidden

- Do not modify `login.html`, `Sidebar.jsx`, or any existing PMS page.
- Do not change the order or content of the existing `## Pages` or `## Data Files` sections of `INDEX.md`.
- Do not add new images, screenshots, or unrelated docs.

## Success criteria

- `INDEX.md` contains a new `## AI Receptionist Admin Prototype` section with the exact table headers and rows above.
- Every admin-* page that exists uses the correct `active="..."` prop on `AdminSidebar` (verify by grep; only patch the `active=` value if wrong).
- `git diff --stat` shows changes only to `INDEX.md` and at most the `active=` line of any admin-* page.
- Write `_runbook/_state/03A.done.md` listing every page that was checked and what (if anything) was patched.
