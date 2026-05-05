# Task 06I — admin-voice.html (NEW)

Build the Voice & Persona configuration page for the dark prototype admin.

## Output

Create exactly one file: `ui_kits/website/_prototype/admin-voice.html`.

## Allow-list

`^ui_kits/website/_prototype/admin-voice\.html$`

## Goal

A clinic owner sees and edits the voice / persona settings from `window.AI_CONFIG[currentClinicId].voice`:
- `assistant_name` (text input, e.g. "Dental AI")
- `provider_title` (select: Doctor / Denturist / Hygienist / Dentist)
- `reason_question` (text input — what the AI asks the caller after greeting)
- `language` (select: English (US) / English (CA) / Spanish (US) / French (CA))

Plus a "Hear it back" preview button (visual only — TTS is engineer-managed).

## Scaffolding

Same as 06F. Load all data scripts + AdminSidebar, mount with `active="voice"`, include OwnerPill.

## Body component

Mount `<AdminSidebar active="voice" clinicName={CLINIC.name} clinicSlug={CLINIC.slug} />` and the AdminTopBar with OwnerPill.

Below the topbar, render:

1. **Page header**:
   - `<h1 className="page-title">Voice & persona</h1>`
   - Subtitle: `What the AI calls itself, what it calls your providers, and what it asks for first.`

2. **Form** — kit-style two-column form (each row label + input):

   - `Assistant name` — text input bound to `voice.assistant_name`. Helper: `This is what the AI says when callers ask "who is this?"`
   - `Provider title` — select bound to `voice.provider_title`. Options: `Doctor`, `Denturist`, `Hygienist`, `Dentist`. Helper: `How the AI refers to the people callers are booking with.`
   - `Reason question` — text input bound to `voice.reason_question`. Default value: `What brings you in?`. Helper: `The first question the AI asks after the greeting.`
   - `Language` — select bound to `voice.language`. Options: `English (US)` (`en-US`), `English (CA)` (`en-CA`), `Spanish (US)` (`es-US`), `French (CA)` (`fr-CA`). Helper: `Voice and recognition default. Engineer-managed if you need a custom voice.`

3. **Preview block** (next to or below the form):
   - Label: `Preview`
   - Subtitle: `Hear how the AI sounds with these settings before saving.`
   - Button: `Hear it back` (ghost-style, visual only).

4. **Save bar** at the bottom: navy `Save voice` button.

## Verbatim required

- `Voice & persona` (in `<title>`, breadcrumb, page-title)
- `What the AI calls itself, what it calls your providers, and what it asks for first.`
- `Assistant name`
- `Provider title`
- `Reason question`
- `Language`
- `Save voice`
- `Hear it back`
- `Denturist`
- `What brings you in?`
- `<AdminSidebar`
- `active="voice"`
- `Rockyridge Dental AI` (in `<title>`)
- `id="rrd-profile-pill"`

## Title

`<title>Voice & persona · Rockyridge Dental AI</title>`

## Breadcrumb

`['Dental AI', 'Configuration', 'Voice & persona']`

## Success criteria

- File size 8–22 KB.
- Verbatim strings all present.
- Mounts `AdminSidebar` with `active="voice"`.
- Has exactly two `<select>` elements (provider_title + language).

## Constraints

- No emoji.
- Use kit form primitives (`field`, `lbl`, `d-input` classes match `admin-routing.html`).
- Definite article: *The Voice. The Reason question.*
- Character constraints: assistant_name max 60, reason_question max 120 (use `maxLength` attribute).
