# Task 06H — admin-disclosure.html (NEW)

Build the AI disclosure configuration page for the dark prototype admin.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-disclosure.html`.

## Allow-list

`^ui_kits/website/_prototype/admin-disclosure\.html$`

## Goal

A clinic owner sees and edits the legal AI disclosure config from `window.AI_CONFIG[currentClinicId].disclosure`:
- A toggle: `ai_disclosure_required` (boolean)
- A textarea: `ai_disclosure_phrase` with character counter (max 280)
- A read-only `last_reviewed_at` line
- A `Save disclosure` button (visual only)
- A small explanation block describing what AI disclosure means and why

The page also surfaces an `Engineer-managed` pill since some compliance changes may require engineer review (mirrors the routing page pattern for `AI SIP URI`).

## Scaffolding

Same as 06F. Load all data scripts + AdminSidebar, mount with `active="disclosure"`, include OwnerPill.

## Body component

Mount `<AdminSidebar active="disclosure" clinicName={CLINIC.name} clinicSlug={CLINIC.slug} />` and the AdminTopBar with OwnerPill.

Below the topbar, render:

1. **Page header**:
   - `<h1 className="page-title">AI disclosure</h1>`
   - Subtitle: `When the AI introduces itself`

2. **Explainer card** (warm-yellow background, parchment border, mirroring the kit's amber callout style):
   `When required by law, the AI must say it's not human at the start of every call.`

3. **Toggle row** (mirrors `_prototype/admin-routing.html` switch pattern):
   - Label: `Disclosure phrase required at the start of every AI call`
   - Switch bound to `ai_disclosure_required`
   - Sub-text: `If your jurisdiction requires AI disclosure, leave this on.`

4. **Disclosure phrase form**:
   - Label: `Disclosure phrase`
   - `<textarea>` bound to `ai_disclosure_phrase`, autosize, maxLength 400
   - Counter: `0 / 280 characters` (red past 280)
   - Helper: `This is the first sentence the AI says when it picks up. Keep it short and clear.`

5. **Last-reviewed line** (read-only, mono small):
   `Last reviewed: 2026-04-01` (formatted from the ISO timestamp)
   With an `Engineer-managed` pill next to it indicating compliance review history is engineer-only.

6. **Save bar** at the bottom: navy `Save disclosure` button.

## Verbatim required

- `AI disclosure` (in `<title>`, breadcrumb, page-title)
- `When the AI introduces itself`
- `When required by law, the AI must say it's not human at the start of every call.`
- `Disclosure phrase`
- `Save disclosure`
- `Engineer-managed`
- `0 / 280 characters`
- `Last reviewed`
- `<AdminSidebar`
- `active="disclosure"`
- `Rockyridge Dental AI` (in `<title>`)
- `id="rrd-profile-pill"`

## Title

`<title>AI disclosure · Rockyridge Dental AI</title>`

## Breadcrumb

`['Dental AI', 'Configuration', 'AI disclosure']`

## Success criteria

- File size 7–22 KB.
- Verbatim strings all present.
- Mounts `AdminSidebar` with `active="disclosure"`.
- Has exactly one `<textarea>` for the disclosure phrase.

## Constraints

- No emoji.
- Use existing `_prototype` switch primitive pattern from `admin-routing.html` (don't invent new switch styles).
- Character counter turns warm-yellow at 240, red at 280.
- Definite article: *The disclosure*. (Used naturally — don't force.)
