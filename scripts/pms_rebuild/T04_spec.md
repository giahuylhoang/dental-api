# T04 — Data layer + auth + providers

## Objective
Port the API client, auth store, MSW mocks, and React Query setup from the Vite app into `web/lib/`. Add `web/app/providers.tsx`. All under Next.js client-component conventions.

## Steps
1. **API client** — copy `frontend/src/api/client.ts` → `web/lib/api/client.ts`.
   - Replace `const BASE = ''` (or equivalent) with `const BASE = process.env.NEXT_PUBLIC_API_URL ?? ''`.
   - Keep `X-Clinic-Id` header logic.
   - Keep 401 auto-refresh with `refreshToken` from `localStorage`.
2. **Auth store** — copy `frontend/src/features/auth/store.ts` → `web/lib/auth/store.ts`.
   - First line: `"use client";`
   - Wrap every direct `localStorage` access in `typeof window !== 'undefined'` guards. The Zustand `persist` middleware is fine; ensure `getStorage`/`storage` is no-op on server.
3. **Auth helpers** — copy `frontend/src/features/auth/auth.ts` → `web/lib/auth/auth.ts` (login/logout/refresh helpers).
4. **Auth guard** — create `web/lib/auth/guard.tsx` (`"use client"`):
   ```tsx
   "use client";
   import { useEffect, useState } from "react";
   import { useRouter } from "next/navigation";
   import { useAuthStore } from "@/lib/auth/store";

   export function AuthGuard({ children }: { children: React.ReactNode }) {
     const router = useRouter();
     const [ready, setReady] = useState(false);
     const user = useAuthStore((s) => s.user);
     useEffect(() => {
       if (!user) { router.replace("/login"); return; }
       setReady(true);
     }, [user, router]);
     if (!ready) return null;
     return <>{children}</>;
   }
   ```
5. **Query client factory** — `web/lib/query/client.ts`:
   ```ts
   import { QueryClient } from "@tanstack/react-query";
   export function makeQueryClient() {
     return new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } } });
   }
   ```
6. **MSW** — copy `frontend/src/mocks/` → `web/lib/mocks/` recursively. Update internal imports (`from "../"` paths → `@/lib/...` or relative as needed). Run `cd web && npx msw init public/ --save` so `web/public/mockServiceWorker.js` exists.
7. **Providers** — create `web/app/providers.tsx`:
   ```tsx
   "use client";
   import { QueryClientProvider } from "@tanstack/react-query";
   import { TooltipProvider } from "@/components/ui/tooltip";
   import { Toaster } from "@/components/ui/sonner";
   import { useEffect, useState } from "react";
   import { makeQueryClient } from "@/lib/query/client";

   export function Providers({ children }: { children: React.ReactNode }) {
     const [client] = useState(() => makeQueryClient());
     useEffect(() => {
       if (process.env.NEXT_PUBLIC_USE_MSW === "true" && typeof window !== "undefined") {
         import("@/lib/mocks/browser").then(({ worker }) =>
           worker.start({ onUnhandledRequest: "bypass" })
         ).catch(() => {});
       }
     }, []);
     return (
       <QueryClientProvider client={client}>
         <TooltipProvider>
           {children}
           <Toaster />
         </TooltipProvider>
       </QueryClientProvider>
     );
   }
   ```
8. Edit `web/app/layout.tsx` to wrap `{children}` in `<Providers>`. Keep design-tokens.css + globals.css imports first.
9. **OpenAPI codegen** — run `cd web && npm run gen:api` so `web/lib/api/v2/types.ts` exists.

## Verify
```
cd web && npx tsc --noEmit && npx next build
```

## Done when
- `web/lib/api/client.ts`, `web/lib/auth/{store.ts,auth.ts,guard.tsx}`, `web/lib/query/client.ts`, `web/lib/mocks/browser.ts`, `web/lib/api/v2/types.ts` all exist.
- `web/app/providers.tsx` exists and is wired into `web/app/layout.tsx`.
- `web/public/mockServiceWorker.js` exists.
- Build clean.
