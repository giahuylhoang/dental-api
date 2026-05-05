# Task 05D — data/ai_config.js (new)

Create the per-clinic AI configuration seed. This is the canonical store for greeting / routing / AI-bookable services / knowledge docs that the four new settings tabs read and write.

## Output

Create exactly one file: `data/ai_config.js`.

## Allow-list

`^data/ai_config\.js$`

## Goal

`window.AI_CONFIG[clinicId]` returns a `{ routing, greeting, ai_bookable_service_ids, knowledge_docs }` object for each of the two clinics.

## File shape (write the file in this exact form, IIFE-wrapped)

```js
// data/ai_config.js — per-clinic AI receptionist configuration for the static prototype.
// Mirrors dental-agent/config/clinics/{id}/{ops,product}.yaml + knowledge/clinics/{id}/*.md shape.
(function () {
  window.AI_CONFIG = {
    "northeast-denture-clinic": {
      routing: {
        timezone: "America/Edmonton",
        ring_timeout_seconds: 5,
        front_desk_numbers: ["+15879738089"],
        backup_number: "+13682990959",
        ai_sip_uri: "sip:34.130.210.160:5060",
        hours: {
          mon: ["09:00", "17:00"],
          tue: ["09:00", "17:00"],
          wed: ["09:00", "19:00"],
          thu: ["09:00", "19:00"],
          fri: ["09:00", "14:00"],
          sat: ["09:00", "18:00"],
          sun: []
        },
        holidays: [],
        ai_after_hours: true,
        ai_in_hours_overflow: true
      },
      greeting: {
        text: "",
        status: "default",
        clinic_approved: true,
        updated_at: null,
        updated_by: null
      },
      ai_bookable_service_ids: ["SVC-001", "SVC-006", "SVC-008"],
      knowledge_docs: [
        {
          filename: "denture_faq.md",
          title: "Denture FAQ",
          last_updated: "2026-04-12",
          word_count: 1840,
          body: "# Denture FAQ\n\nCommon questions callers ask about dentures, fittings, and aftercare. Used by the AI to answer FAQ-style questions before transferring to the front desk."
        },
        {
          filename: "practice_info.md",
          title: "Practice Info",
          last_updated: "2026-04-08",
          word_count: 920,
          body: "# Practice Info\n\nClinic location, parking, accessibility, accepted insurance, and what to bring to a first visit."
        }
      ]
    },
    "market-mall-denture": {
      routing: {
        timezone: "America/Edmonton",
        ring_timeout_seconds: 4,
        front_desk_numbers: ["+13682990959"],
        backup_number: "+15879738089",
        ai_sip_uri: "sip:34.130.210.161:5060",
        hours: {
          mon: ["09:00", "17:00"],
          tue: ["09:00", "17:00"],
          wed: ["09:00", "17:00"],
          thu: ["09:00", "17:00"],
          fri: ["09:00", "17:00"],
          sat: [],
          sun: []
        },
        holidays: [],
        ai_after_hours: true,
        ai_in_hours_overflow: false
      },
      greeting: {
        text: "Market Mall Denture Clinic, how can I help?",
        status: "approved",
        clinic_approved: true,
        updated_at: "2026-04-20T14:00:00Z",
        updated_by: "giahuy.l.hoang@gmail.com"
      },
      ai_bookable_service_ids: ["SVC-001", "SVC-006", "SVC-007", "SVC-008"],
      knowledge_docs: [
        {
          filename: "denture_faq.md",
          title: "Denture FAQ",
          last_updated: "2026-04-15",
          word_count: 1620,
          body: "# Denture FAQ\n\nMarket Mall variant — same denture FAQ topics, slightly different aftercare instructions for partials."
        },
        {
          filename: "practice_info.md",
          title: "Practice Info",
          last_updated: "2026-04-15",
          word_count: 740,
          body: "# Practice Info\n\nMarket Mall location, parking inside the mall, mall-hour overlaps, and accepted insurance."
        }
      ]
    }
  };
})();
```

## Verbatim required

- `window.AI_CONFIG`
- `northeast-denture-clinic`
- `market-mall-denture`
- `routing`
- `greeting`
- `ai_bookable_service_ids`
- `knowledge_docs`
- `denture_faq.md`
- `practice_info.md`
- `+15879738089`
- `+13682990959`
- `sip:34.130.210.160:5060`
- `Market Mall Denture Clinic, how can I help?`
- `clinic_approved`
- `pending_review` *(reserved status name; include as a comment block at the top of the file documenting the four valid status values: default, pending_review, approved, archived)*
- `SVC-001`

## Forbidden

- Adding clinics beyond the two listed above.
- Inventing service ids that don't exist in `data/services.js` (only `SVC-001` … `SVC-008` are valid).

## Success criteria

- File size between 4 KB and 20 KB.
- `knowledge_docs` array appears exactly twice (once per clinic).
- Both clinics have a `routing`, `greeting`, `ai_bookable_service_ids`, and `knowledge_docs` key.
- The Northeast greeting `text` is empty string (so the UI shows the "No custom greeting persisted yet" state).
- The Market Mall greeting status is `"approved"`.

## Constraints

- Order keys per clinic: `routing, greeting, ai_bookable_service_ids, knowledge_docs`.
- Keep the comment header explaining the dental-agent yaml mirror.
- Add a 1-3 line comment documenting the four valid greeting status values: `default`, `pending_review`, `approved`, `archived`.
