# Task 06G — admin-knowledge.html (NEW)

Build the per-clinic Knowledge / FAQ editor page for the dark prototype admin.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-knowledge.html`.

## Allow-list

`^ui_kits/website/_prototype/admin-knowledge\.html$`

## Goal

A clinic owner sees every markdown KB doc from `window.AI_CONFIG[currentClinicId].knowledge_docs` as a list of expandable cards. Each card shows filename, title, last_updated, word_count. Clicking expands to reveal a textarea bound to the doc body (dirty-tracking visual only — no real save).

## Scaffolding

Same as 06F (admin-services.html). Load all required data scripts + AdminSidebar, mount with `active="knowledge"`, include OwnerPill.

## Body component

Mount `<AdminSidebar active="knowledge" clinicName={CLINIC.name} clinicSlug={CLINIC.slug} />` and the inline AdminTopBar with OwnerPill.

Below the topbar, render:

1. **Page header**:
   - `<h1 className="page-title">The Knowledge base</h1>`
   - Subtitle: `Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions.`

2. **Doc list** — for each `doc` in `AI_CONFIG[currentClinicId].knowledge_docs`:
   ```
   ┌──────────────────────────────────────────────────────────────┐
   │ denture_faq.md                                               │  (mono, top-left)
   │ Denture FAQ                                                  │  (Display 600, navy)
   │ Last updated: 2026-04-12     Word count: 1840          [▼]  │  (right-aligned metadata)
   └──────────────────────────────────────────────────────────────┘
   ```
   Click the row → expand below to show a `<textarea>` bound to `doc.body`. Re-click chevron → collapse.
   Use `React.useState` for the open/closed state per doc (use a `Set` or `{[filename]: bool}` map).

3. **Empty state** — if `knowledge_docs.length === 0`:
   `No knowledge yet. Drop a markdown file in to give the agent something to draw on.`

4. **Save bar** at the bottom: navy `Save knowledge updates` button (visual only).

## Verbatim required

- `Knowledge` (in title and breadcrumb)
- `The Knowledge base`
- `Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions.`
- `Last updated`
- `Word count`
- `Save knowledge updates`
- `denture_faq.md`
- `practice_info.md`
- `No knowledge yet. Drop a markdown file in to give the agent something to draw on.`
- `<AdminSidebar`
- `active="knowledge"`
- `Rockyridge Dental AI` (in `<title>`)
- `id="rrd-profile-pill"`

## Title

`<title>Knowledge · Rockyridge Dental AI</title>`

## Breadcrumb

`['Dental AI', 'Configuration', 'Knowledge']`

## Success criteria

- File size 8–28 KB.
- Verbatim strings all present.
- `assert_grep_count "<textarea" 1 6` — at least one textarea, at most six (one per doc + maybe a few more for collapsed state).
- Mounts `AdminSidebar` with `active="knowledge"`.

## Constraints

- Mono font for filename rows.
- Display font for titles.
- No emoji.
- Use Lucide-shaped chevron icons.
- Definite article on system names.
