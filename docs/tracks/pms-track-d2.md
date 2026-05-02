# PMS Module D2 — Patient context primitives (the user's pain)

Make `make test-pms-d2` exit 0.

## Why

The user said: *"every section refers to patient id which is very hard to see — make it easier to look at the patient info"* and *"patient searching is not working across sections"*. There are 4 hand-rolled patient typeaheads, no shared `usePatient` hook, no chip component. D2 ships the three primitives that fix both problems.

## Success criteria

### 1. `frontend/src/features/patients/usePatient.ts`

```ts
export function usePatient(id?: string | null): {
  patient: Patient | null;
  isLoading: boolean;
  error: Error | null;
}
```

- Wraps `useQuery({ queryKey: ['patient', id], queryFn: () => fetcher(`/api/patients/${id}`), enabled: !!id, staleTime: Infinity })`.
- Returns `{ patient: null, isLoading: false, error: null }` if `id` is falsy.
- The query key is shared so multiple components asking for the same id share a cache.

### 2. `frontend/src/features/patients/PatientChip.tsx`

```tsx
<PatientChip patientId={id} variant="inline | card | breadcrumb" linkTo="/patients/:id" />
```

- `inline` variant (default): small horizontal chip — initials avatar (rounded-full, action-color bg) + name. ~24px tall.
- `card` variant: bigger — initials avatar + name + phone (smaller line under name).
- `breadcrumb` variant: name only, styled as a link (used in headers).
- While `usePatient` is loading: `<Skeleton className="h-5 w-32" />`.
- If `usePatient` errors with 404: render the abbreviated id (`p1…`) wrapped in a `<span title="Patient not found">`.
- If `linkTo` is provided, the whole chip is a `<Link to={linkTo.replace(':id', patientId)}>`.

### 3. `frontend/src/features/patients/PatientSearchInput.tsx`

```tsx
<PatientSearchInput
  onSelect={(patient) => void}
  placeholder="Search patients…"
  initialValue?: string
  autoFocus?: boolean
/>
```

- Uses D1 `<Command>` (cmdk-based) under the hood.
- Debounces input by 200ms before fetching.
- Hits `GET /api/patients?q={query}&limit=10`.
- Render results: avatar initials + name + (phone or DOB underneath).
- Empty state: "No patients found".
- Loading: `<Skeleton>` rows.
- Error state: small inline error.
- `onSelect` fires with the full patient object (not just id).

### 4. Replace the 4 hand-rolled searches

In each of these files, swap the existing patient typeahead implementation for `<PatientSearchInput onSelect={...}>`:

- `frontend/src/features/communications/ComposeDialog.tsx` (M1's autocomplete)
- `frontend/src/features/scheduling/NewAppointmentDialog.tsx`
- `frontend/src/features/treatment-plans/TreatmentPlansPage.tsx`
- `frontend/src/features/patients/PatientList.tsx` (top search bar)

Don't break the existing tests for these files (M1, M4, F1 etc.) — keep their published prop APIs stable.

### 5. Add patient context where missing

In each, render `<PatientChip patientId={...} />` where currently nothing or just an id is shown:

- `frontend/src/features/lab/LabCaseKanban.tsx` cards — add the chip above the case_number.
- `frontend/src/features/lab/LabCaseDrawer.tsx` header — add `variant="breadcrumb"`.
- `frontend/src/features/scheduling/Scheduler.tsx` — when building the FullCalendar event title, prepend the patient name (resolved via `usePatient(event.patient_id)`). If still loading, fall back to "Loading…" (FullCalendar updates titles on re-render).
- `frontend/src/features/scheduling/AppointmentDrawer.tsx` header — `<PatientChip variant="card" />` instead of the plain link.

## Tests first (`frontend/tests/track_pms_d2/`)

1. **`use-patient-hook.test.tsx`** — render two components calling `usePatient('p1')` inside the same QueryClient; assert mocked GET fires once (not twice).

2. **`patient-chip-renders-name.test.tsx`** — `<PatientChip patientId="p1" />` with MSW returning `{ id: 'p1', first_name: 'Alice', last_name: 'Smith' }`; `await waitFor` then assert "Alice Smith" visible.

3. **`patient-chip-fallback-on-404.test.tsx`** — MSW returns 404; chip shows `p1…` (truncated) with title attribute.

4. **`patient-chip-variants.test.tsx`** — `inline` shows just name; `card` shows name + phone; `breadcrumb` shows name as a link element.

5. **`patient-search-debounces.test.tsx`** — render the search input; type "a", "al", "ali", "alic", "alice" within 100ms each; advance fake timers 250ms; assert mocked GET was called exactly ONCE with `?q=alice`.

6. **`patient-search-onselect-fires.test.tsx`** — type "ali"; mock returns Alice; click Alice in the list; assert `onSelect` called with the full patient object (incl. id, first_name, last_name).

7. **`compose-dialog-uses-shared-search.test.tsx`** — render M1 ComposeDialog; assert `<PatientSearchInput>` is mounted (use `data-testid="patient-search"` selector).

8. **`lab-card-shows-patient-chip.test.tsx`** — render LabCaseKanban with a mocked case linked to a patient; assert the chip renders the resolved name on the card.

## Implementation guidance

- Initials: take first character of `first_name` + first character of `last_name`. If name format is `"First Last"`, split.
- Avatar bg: hash the patient id to a hue, use `bg-[hsl(var(--ds-action-500-h)_70%_85%)]` style — or just use the action color and let initials carry uniqueness.
- Use the existing `frontend/src/api/client.ts` `fetcher` — never call `fetch` directly (that bypasses the auth header).
- Reuse D1 `<Skeleton>`, `<Badge>`, `<Command>`.
- Add a `data-testid="patient-chip"` to the chip root and `data-testid="patient-search"` to the search root.

## Constraints

- All M1, M4, F1, F4 tests must stay green — preserve existing public component APIs.
- v1 contract stays untouched.
- Don't add new backend endpoints — `/api/patients?q=` and `/api/patients/{id}` already exist.

```bash
make test-pms-d2
```
