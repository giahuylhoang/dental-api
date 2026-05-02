# PMS Module M2 — Documents drag-drop (TDD)

Make `make test-pms-m2` exit 0. Tests first, then code.

## Success criteria

- `DocumentUploader` rebuilt on top of **`react-dropzone`** (already installed: `npm i react-dropzone` done).
- Multi-file accepted (up to 10 per drop). Each file gets its own row in a "queued uploads" list.
- Per-file progress bar driven by **XMLHttpRequest progress events** (NOT `fetch`, which has no progress in browsers). Width = `loaded/total*100`.
- Per-file error UI: failed network or rejected mime → red error + "Retry" button.
- Queue auto-clears successful uploads after 2s; failed ones stay until dismissed.
- Insurance Documents sub-tab on Patient360: filters list by `kind='insurance'`. Add a kind filter on the existing `DocumentList`.

## Tests first (`frontend/tests/track_pms_m2/`)

1. **`dropzone-renders.test.tsx`** — mount `<DocumentUploader patientId="p1" />`, find element with `[data-testid="dropzone"]` (or by role). Simulate `drop` event with 3 File objects → assert 3 rows in queue list.

2. **`progress-bar-updates.test.tsx`** — mock `XMLHttpRequest`. Trigger an upload, fire `progress` events with `loaded=50, total=100` → assert progress bar style width is `50%`.

3. **`failed-upload-shows-error.test.tsx`** — mock XHR error event → assert error message + "Retry" button visible. Click Retry → new XHR created.

E2E (`frontend/e2e/track_pms_m2/`):
- Login → /patients/{id} → Documents tab → drop 2 small in-memory files via `setInputFiles` → both appear → both reach 100% → both rows show green checkmark.

## Implementation

- Modify `frontend/src/features/patients/DocumentUploader.tsx`:
  - `useDropzone({ multiple: true, accept: { 'image/*': [], 'application/pdf': [], 'application/msword': [] }, onDrop })`
  - Maintain `queue: { file, progress, status: 'pending'|'uploading'|'done'|'error' }[]` state.
  - For each file: spawn an `XMLHttpRequest` with `upload.onprogress` setting `progress`, on `load` mark done.
  - Use `POST /api/v2/clinical/documents/upload` (multipart). Add `kind` field from a select.
- Modify `frontend/src/features/patients/DocumentList.tsx`: accept optional `kindFilter` prop.
- In `Patient360.tsx`: add a sub-tab "Insurance documents" under the existing Documents tab — passes `kindFilter="insurance"`.

## Constraints

- Don't break the existing `kind` selector and single-file backward-compat — multi-file is the new default but a single-file scenario must still work.
- Don't change the backend upload endpoint behavior.

```bash
make test-pms-m2
```
