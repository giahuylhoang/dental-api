# Task 05L — login.html copy edit

Replace one phrase in the login marketing copy: "Sign in to your clinic" → "Sign in to your workspace". This reframes the entry point from clinic-scoped to owner-scoped without touching auth code.

## Output

Modify exactly one file: `ui_kits/website/login.html`.

## Allow-list

`^ui_kits/website/login\.html$`

## Goal

A clinic owner who manages multiple clinics doesn't sign in to one — they sign in to the workspace that contains all of them. The copy should reflect that.

## Approach

Find the line that contains `Sign in to your clinic` (it's around line 79 in the current file, formatted like `Sign in to your clinic · Sovereign · Audit-logged` or similar). Change only the phrase `Sign in to your clinic` to `Sign in to your workspace`. Preserve the surrounding bullet separator characters and any sibling phrases ("Sovereign", "Audit-logged", etc.) byte-identical.

Do not touch:
- The `<title>`
- Any `<script>` block
- The brand wordmark `ROCKYRIDGE / DENTAL AI`
- The `LoginCard.jsx` mount or the form fields
- Any CSS

## Verbatim required (post-task)

- `Sign in to your workspace`

## Forbidden (post-task)

- The string `Sign in to your clinic` must NOT appear anywhere in the file.

## Success criteria

- File size delta within ±5% of pre-task size.
- `Sign in to your workspace` appears at least once.
- `Sign in to your clinic` does NOT appear.
- The login form structure is otherwise byte-identical.

## Constraints

- Surgical edit only. Do not reformat surrounding markup.
