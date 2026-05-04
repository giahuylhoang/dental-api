# T01 — Scaffold Next.js 15 App Router at /web

## Objective
Create a Next.js 15 App Router project at `/Users/giahuyhoangle/Projects/dental-api/web/` (sibling of `frontend/`). Vite app at `frontend/` must remain untouched and runnable.

## Steps
1. From `/Users/giahuyhoangle/Projects/dental-api/`, run:
   ```
   npx --yes create-next-app@latest web --ts --tailwind --eslint --app --no-src-dir --use-npm --import-alias "@/*"
   ```
   (Pin Tailwind v3 if the CLI defaults to v4; the project standardizes on Tailwind 3.4.)
2. `cd web` and install runtime dependencies (mirror current `frontend/package.json` minus `react-router-dom`):
   - shadcn/Radix surface: `@radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-popover @radix-ui/react-scroll-area @radix-ui/react-select @radix-ui/react-separator @radix-ui/react-switch @radix-ui/react-tabs @radix-ui/react-toast @radix-ui/react-tooltip class-variance-authority clsx tailwind-merge tailwindcss-animate lucide-react sonner`
   - Data + state: `@tanstack/react-query @tanstack/react-table zustand react-hook-form @hookform/resolvers zod`
   - Calendar: `@fullcalendar/core @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction @fullcalendar/react`
   - Editor + PDF: `@tiptap/react @tiptap/pm @tiptap/starter-kit @react-pdf/renderer`
   - Misc: `cmdk fuse.js react-dropzone react-resizable-panels @dnd-kit/core @dnd-kit/sortable`
   - Mocks + codegen: `msw openapi-typescript`
3. Create `web/.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8001
   NEXT_PUBLIC_USE_MSW=true
   ```
4. Replace `web/next.config.mjs` with rewrites that proxy `/api/*` to FastAPI in dev:
   ```js
   /** @type {import('next').NextConfig} */
   const nextConfig = {
     async rewrites() {
       if (process.env.NODE_ENV !== 'development') return [];
       const target = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8001';
       return [{ source: '/api/:path*', destination: `${target}/api/:path*` }];
     },
   };
   export default nextConfig;
   ```
5. Edit `web/package.json` scripts:
   - `"dev": "next dev -p 3001"`
   - keep `build`, `start`, `lint`
   - add `"gen:api": "openapi-typescript ../docs/openapi-v2.yaml -o lib/api/v2/types.ts"`
6. Add `web/.gitignore` entries for `.next/`, `node_modules/`, `coverage/`, `playwright-report/` (likely already present from create-next-app).
7. Verify: `cd web && npx next build` exits 0.

## Constraints
- DO NOT modify `/Users/giahuyhoangle/Projects/dental-api/frontend/`.
- Use Tailwind v3 (not v4). If create-next-app installs v4, downgrade with `npm i -D tailwindcss@^3.4 postcss autoprefixer` and run `npx tailwindcss init -p`.
- TypeScript strict mode on (default).

## Done when
- `web/package.json`, `web/next.config.mjs`, `web/.env.local` exist and match the contract.
- `web/app/layout.tsx`, `web/app/page.tsx`, `web/app/globals.css` exist (default scaffold OK; T02 will re-edit them).
- `cd web && npx next build` succeeds.
