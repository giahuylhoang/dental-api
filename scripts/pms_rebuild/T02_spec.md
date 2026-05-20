# T02 — Tokens + Tailwind config

## Objective
Wire the Rockyridge design tokens into the Next.js app and configure Tailwind to consume them. Zero raw hex outside the tokens file.

## Steps
1. Copy verbatim:
   ```
   cp /Users/giahuyhoangle/Projects/clone-website/rockyridgeai-dental.com/colors_and_type.css \
      /Users/giahuyhoangle/Projects/dental-api/web/styles/design-tokens.css
   ```
   Create `web/styles/` if missing.
2. Edit `web/app/layout.tsx` so the imports are exactly:
   ```ts
   import "../styles/design-tokens.css";
   import "./globals.css";
   ```
3. Edit `web/app/globals.css` to keep `@tailwind base; @tailwind components; @tailwind utilities;` and remove the create-next-app default body resets that conflict with token-driven colors.
4. Replace `web/tailwind.config.ts` with a config that:
   - `darkMode: ['class']`
   - `content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}']`
   - `theme.extend.colors` with semantic vars (each as `hsl(var(--TOKEN) / <alpha-value>)`):
     - `background, foreground`
     - `primary: { DEFAULT, foreground }`
     - `secondary: { DEFAULT, foreground }`
     - `muted: { DEFAULT, foreground }`
     - `accent: { DEFAULT, foreground }`
     - `card: { DEFAULT, foreground }`
     - `popover: { DEFAULT, foreground }`
     - `destructive: { DEFAULT, foreground }`
     - `success: { DEFAULT, foreground }`
     - `warning: { DEFAULT, foreground }`
     - `border, input, ring`
     - `sidebar: { DEFAULT, foreground, primary, 'primary-foreground', accent, 'accent-foreground', border, ring }`
     - `chart: { 1, 2, 3, 4, 5 }`
   - `theme.extend.borderRadius`: `sm,md,lg,xl` from `var(--radius-*)`.
   - `theme.extend.boxShadow`: `xs,sm,md,lg,xl` from `var(--shadow-*)`.
   - `theme.extend.fontFamily`: `display: ['var(--font-display)', 'serif']`, `sans: ['var(--font-ui)', 'sans-serif']`, `mono: ['var(--font-mono)', 'monospace']`.
   - `plugins: [require('tailwindcss-animate')]`.
   Inspect the actual token names in `web/styles/design-tokens.css` first — only bind vars that exist there; if a token is missing, omit it (do not invent).
5. Edit `web/app/page.tsx` to render a tiny smoke screen using token classes (`bg-background text-foreground`) so build verifies tokens resolve. Example:
   ```tsx
   export default function Home() {
     return (
       <main className="min-h-screen bg-background text-foreground p-10 font-sans">
         <h1 className="font-display text-3xl">Tokens loaded</h1>
       </main>
     );
   }
   ```
6. Run: `cd web && npx next build`.

## Constraints
- No raw hex anywhere under `web/{app,components,lib}` outside of `web/styles/design-tokens.css`.
- Do not modify `frontend/`.

## Done when
- `web/styles/design-tokens.css` exists and is identical to the source.
- `web/tailwind.config.ts` binds the semantic tokens above.
- `cd web && npx next build` succeeds.
- `! grep -RInE '#[0-9A-Fa-f]{3,8}\b' web/app web/components web/lib 2>/dev/null | grep -v node_modules` is empty (folders may not exist yet — that's fine).
