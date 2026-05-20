# PMS Module M4 — CRM full CRUD (TDD)

Make `make test-pms-m4` exit 0.

## Success criteria

- LeadKanban toolbar has **"+ New Lead"** button → opens `LeadCreateDialog`.
- `LeadCreateDialog`: fields first_name, last_name, phone, email, source (dropdown: phone/web/referral/walk-in/other), notes. Submit → `POST /api/v2/crm/leads` (M0 endpoint). On success, kanban refetches.
- Card click → `LeadDrawer`:
  - Detail tab: editable fields, owner dropdown (lists active providers — `GET /api/providers`), status dropdown (NEW/CONTACTED/QUALIFIED/CONVERTED/LOST). Save → PUT `/api/v2/crm/leads/{id}`.
  - Activities tab: timeline of activities (`GET /api/v2/crm/leads/{id}/activities`). `AddActivityForm` at the top — kind dropdown (note/call/email/meeting), body textarea, submit → POST `/activities`. Timeline shows author + timestamp.
  - "Convert to patient" button (existing endpoint).

## Tests first (`frontend/tests/track_pms_m4/`)

1. **`lead-create-dialog.test.tsx`** — mount `<LeadCreateDialog open onClose />`, fill name+phone, click Save, mock POST; assert request body matches.

2. **`lead-drawer-renders.test.tsx`** — mount with `leadId='L1'`, mock GET responses; assert lead name + activities tab visible.

3. **`add-activity.test.tsx`** — mount drawer activities tab, type note body, submit, mock POST; assert mocked called with `{kind:'note', body:'...'}`. After mutation, list refreshes.

4. **`assign-owner.test.tsx`** — open detail tab, change owner dropdown, click Save; mock PUT; assert PUT body has `owner_id`.

E2E (`frontend/e2e/track_pms_m4/`):
- /crm → "+ New Lead" → fill form → save → card appears in NEW column → click card → drawer → switch to Activities → add note "First call done" → close drawer → reopen → note persists.

## Implementation files

- New: `frontend/src/features/crm/LeadCreateDialog.tsx`
- New: `frontend/src/features/crm/LeadDrawer.tsx` (uses shared `Drawer`)
- New: `frontend/src/features/crm/LeadActivityTimeline.tsx`
- New: `frontend/src/features/crm/AddActivityForm.tsx`
- Modify: `frontend/src/features/crm/LeadKanban.tsx` (add "+ New Lead" button + click → drawer)

## Constraints

- Don't break drag-to-change-status on the kanban (it currently calls PUT `/api/leads/{id}/status` — keep that).
- All POSTs use `fetcher` with `X-Clinic-Id` header (already in client).
- M0 ships these endpoints; assume they exist.

```bash
make test-pms-m4
```
