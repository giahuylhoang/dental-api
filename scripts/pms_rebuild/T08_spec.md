# T08 — /patients + /patients/[id]

## Objective
Build the patient list and Patient360 detail page.

## References
- Visual: `ui_kits/website/patients.html` and `patient-detail.html`
- Logic: `frontend/src/features/patients/{PatientList,Patient360,ToothChart,InsuranceList,DocumentList,NotesPanel,MedicalForm,LifecyclePanel,QuickBookPopover,usePatient}.tsx`

## /patients (list)
- Page header with search + status filter chips (`FilterChips`).
- `DataTable` of patients (id, name, dob, phone, status, lifecycle).
- Pagination via existing `/api/patients?page=X&limit=Y`.
- Quick-book popover wraps shadcn Popover.
- Row click → `next/link` to `/patients/{id}`.

## /patients/[id] (Patient360)
- Tabs (via `@/components/dental/Tabs`): Overview, Appointments, Denture cases, Documents, Tooth chart, Notes, Insurance, Medical, Lifecycle.
- ToothChart canvas: `"use client"` + dynamic import if it touches `window`.
- Notes panel: Tiptap editor — `dynamic(() => import(...), { ssr: false })`.
- Insurance: list + delete drawer; uses `Drawer`.
- Documents: react-dropzone uploader (`"use client"`).
- Lifecycle: status promotion form.
- All data calls go through `fetcher()` exactly as in the Vite version (same endpoint paths + query keys).

## Verify
```
cd web && npx tsc --noEmit && npx next build
```
