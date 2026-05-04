# T06 — AppShell + (portal)/(app) groups

## Objective
Create the route groups, layout shell, and the `DynamicCalendar` wrapper. Wire login.

## Steps
1. **AppShell** — `web/components/layout/AppShell.tsx` (`"use client"`):
   ```tsx
   "use client";
   import { Sidebar } from "@/components/dental/Sidebar";
   import { TopBar } from "@/components/dental/TopBar";

   export function AppShell({ children }: { children: React.ReactNode }) {
     return (
       <div className="min-h-screen bg-background text-foreground flex">
         <Sidebar />
         <div className="flex-1 flex flex-col">
           <TopBar />
           <main className="flex-1 p-6">{children}</main>
         </div>
       </div>
     );
   }
   ```
2. **DynamicCalendar** — `web/components/layout/DynamicCalendar.tsx`:
   ```tsx
   "use client";
   import dynamic from "next/dynamic";
   export const FullCalendar = dynamic(() => import("@fullcalendar/react"), { ssr: false });
   ```
3. **Root layout** — `web/app/layout.tsx`: keep token + globals imports first; wrap `<body>` content in `<Providers>`. Apply `font-sans` + `bg-background text-foreground` to `<body>`.
4. **Portal group**:
   - `web/app/(portal)/layout.tsx`:
     ```tsx
     export default function PortalLayout({ children }: { children: React.ReactNode }) {
       return <div className="dark min-h-screen bg-background text-foreground">{children}</div>;
     }
     ```
   - `web/app/(portal)/login/page.tsx` (`"use client"`): renders `LoginCard` with an `onSubmit` that calls `login()` from `@/lib/auth/auth` and on success runs `useRouter().push("/dashboard")`.
5. **App group**:
   - `web/app/(app)/layout.tsx` (`"use client"`):
     ```tsx
     "use client";
     import { AuthGuard } from "@/lib/auth/guard";
     import { AppShell } from "@/components/layout/AppShell";
     export default function AppLayout({ children }: { children: React.ReactNode }) {
       return (
         <AuthGuard>
           <AppShell>{children}</AppShell>
         </AuthGuard>
       );
     }
     ```
6. **Root `/`** — `web/app/page.tsx`:
   ```tsx
   import { redirect } from "next/navigation";
   export default function Page() { redirect("/dashboard"); }
   ```
7. **404** — `web/app/not-found.tsx` rendering `EmptyState` with a "Page not found" message and a back link to `/dashboard`.
8. Stub each `(app)` route with a placeholder `page.tsx` so build passes:
   - `dashboard, patients, patients/[id], schedule, lab, billing, communications, crm, plans, reports, settings` — each just `export default function Page() { return <div>TODO</div>; }`. T07–T13 will fill them in.

## Verify
```
cd web && npx tsc --noEmit && npx next build && (cd web && (timeout 8 npx next dev -p 3001 || true))
```
(The `next dev` invocation is just to confirm boot; not required for CI.)

## Done when
- All listed files exist.
- `tsc --noEmit` and `next build` clean.
- Visiting `/` redirects to `/dashboard` (which now requires auth → bounces to `/login`).
