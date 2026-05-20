# PMS Module D3 — Global patient search via ⌘K

Make `make test-pms-d3` exit 0.

## Why

M5 shipped a ⌘K command palette but its placeholder text "Search patients, invoices, appointments…" lies — patient search is **not wired**. D3 finally hooks `<PatientSearchInput>` (D2) into `CommandPalette.tsx` so the user can jump to any patient from any page.

## Success criteria

Modify `frontend/src/features/search/CommandPalette.tsx`:

- Add a top-level **Patients** section above "Quick actions".
- When the user types, debounce → `/api/patients?q=`. Show top 5 matches.
- Each match: initials avatar + first/last name + phone (small, secondary text).
- Pressing Enter on a selected patient: `useNavigate` → `/patients/{id}` AND call `markVisited('patient', id, label)` (existing M5 helper) to remember.
- When the input is empty: show the existing "Recently viewed" section first, then "Quick actions". Don't fire a search request when query is empty.
- Replace the placeholder text "Search patients, invoices, appointments…" with the real wired UI; the placeholder may stay as input placeholder text but the section behavior must work.
- Keyboard: ⌘K from any authenticated page opens the palette (existing M5 hook stays). Esc closes it.

## Tests first (`frontend/tests/track_pms_d3/`)

1. **`palette-shows-patient-results.test.tsx`** — open palette; type "ali"; mock `/api/patients?q=ali` returns Alice; assert "Alice" visible under a "Patients" section group.

2. **`palette-enter-navigates.test.tsx`** — same setup; press ArrowDown then Enter; assert `useNavigate` was called with `/patients/<alice-id>`.

3. **`palette-empty-shows-recent-first.test.tsx`** — `localStorage.setItem('pms.recentlyViewed', JSON.stringify([{kind:'patient', id:'p1', label:'Alice'}, ...]))`; open palette without typing; assert "Recently viewed" section visible above "Quick actions"; assert NO `/api/patients?q=` request was fired.

4. **`palette-marks-visited-on-select.test.tsx`** — open palette; type "ali"; select Alice; assert `localStorage.pms.recentlyViewed` was updated to include Alice at the top.

## Implementation guidance

- Use D2's `usePatientSearch` (or whatever D2 exposed) — if D2 only exposed the input component, you can use `useQuery(['patients-search', q], () => fetcher(...))` directly here with a 200ms debounce.
- The "Patients" section must render BEFORE "Quick actions" (visual order).
- Don't break existing M5 tests (`frontend/tests/track_pms_m5/`).

## Constraints

- Don't add a new backend endpoint — `/api/patients?q=` is enough.
- Don't move the keyboard handler — M5's existing handler stays.

```bash
make test-pms-d3
```
