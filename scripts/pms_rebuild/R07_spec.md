# R07 — /communications from communications.html

Read `R_SHARED_spec.md` first.

## Source
`/Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/ui_kits/website/communications.html`

## Target
`/Users/giahuyhoangle/Projects/dental-api/web/app/(app)/communications/page.tsx` (overwrite)

## Composition
1. Page header.
2. **4-column KPI strip**: total threads, unread, response time, etc. (port HTML's exact labels).
3. **Two-column layout**:
   - Left: thread list with channel chips (SMS / Email / Voice) + search + unread indicators.
   - Right: thread detail with avatar+name header, message bubbles, action buttons.
4. **Composer area** at bottom of right pane → render `<LockedFeature title="Composer" body="The composer is paused while we redesign the templating layer." backHref="/communications" />` — keep this lock per user's earlier decision.

## Data wiring
- Threads → `/api/v2/communications/threads` (existing).
- Thread messages → `/api/v2/communications/threads/{id}/messages` (existing).

## Done when
- Two-column inbox layout matches HTML.
- Composer area renders LockedFeature.
- `cd web && npx next build` green.
