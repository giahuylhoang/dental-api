# T14 — Verification gate

## Objective
Hard gate: lint, type-check, full build, Playwright smoke pass.

## Steps
1. `cd web && npm run lint`
2. `cd web && npx tsc --noEmit`
3. `cd web && npx next build`
4. **Token guard:** `! grep -RInE '#[0-9A-Fa-f]{3,8}\b' web/app web/components web/lib | grep -v design-tokens.css`
5. **Inline-style guard:** `! grep -RIn 'style={{' web/app web/components | grep -v node_modules | grep -v 'Pdf\|@react-pdf'`
6. Add `web/playwright.config.ts` that boots `next dev -p 3001` as `webServer`. Add `web/e2e/smoke.spec.ts`:
   - `/login` renders LoginCard (dark theme).
   - Mock-authenticated session loads each route: `/dashboard, /patients, /patients/[id]?id=mock-id, /schedule, /lab, /billing, /communications, /crm, /plans, /reports, /settings`.
   - `/plans` shows overline "Engineering Decision: Locked".
   - `/communications` composer area shows the locked overline.
   - `/settings` shows ≥2 locked overlays.
   - `/reports` shows ≥1 locked overlay.
7. Run: `npx playwright install --with-deps chromium && npx playwright test`

## Done when
All checks exit 0.
