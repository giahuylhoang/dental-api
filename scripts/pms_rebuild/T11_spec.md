# T11 — /communications + /crm (one locked overlay)

## Objective
Communications inbox (composer locked); CRM lead Kanban with drawer.

## References
- Visual: `ui_kits/website/{communications.html,crm.html,lead-detail.html}`
- Logic: `frontend/src/features/communications/*` and `frontend/src/features/crm/*`

## /communications
- ThreadList + ThreadDetail (read-only message list with `MessageBubble`).
- **Composer area is locked**: render
  ```tsx
  <LockedFeature
    title="Composer"
    body="The composer is paused while we redesign the templating layer."
    backHref="/communications"
  />
  ```
  in place of the editor.

## /crm
- `LeadKanban` board (dnd-kit) by lead status.
- `LeadDrawer` (Sheet) with form + activity timeline.
- `AddActivityForm` posts to existing `/api/leads/{id}/activities`.

## Verify
```
cd web && npx tsc --noEmit && npx next build
```
