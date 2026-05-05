// data/ai_config.js — per-clinic AI receptionist configuration for the static prototype.
// Mirrors dental-agent/config/clinics/{id}/{ops,product}.yaml + knowledge/clinics/{id}/*.md shape.
//
// Valid greeting status values: default, pending_review, approved, archived
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
          body: "# Denture FAQ\n\nCommon questions callers ask about dentures, fittings, and aftercare. Used by the AI to answer FAQ-style questions before transferring to the front desk.\n\n## What are dentures?\nDentures are removable prosthetic devices designed to replace missing teeth. They are supported by the surrounding soft and hard tissues of the oral cavity. Complete dentures replace all teeth in an arch, while partial dentures fill gaps where some natural teeth remain.\n\n## How long does a fitting take?\nA standard fitting appointment is 45 to 60 minutes. The denturist takes impressions, checks bite alignment, and discusses material options with the patient.\n\n## What aftercare is recommended?\nRemove dentures at night to let gum tissue rest. Clean daily with a soft brush and denture cleanser. Attend follow-up appointments as scheduled to check fit and tissue health."
        },
        {
          filename: "practice_info.md",
          title: "Practice Info",
          last_updated: "2026-04-08",
          word_count: 920,
          body: "# Practice Info\n\nClinic location, parking, accessibility, accepted insurance, and what to bring to a first visit.\n\n## Location\nNortheast Denture Clinic is located at the northeast corner of the city, with convenient access from major transit routes and free surface parking.\n\n## Accepted Insurance\nWe accept most major dental insurance plans. Patients should bring their insurance card and a valid photo ID to their first appointment.\n\n## What to Bring\nNew patients should arrive 15 minutes early with their insurance information, a list of current medications, and any previous dental records or X-rays they have available."
        }
      ],
      disclosure: {
        ai_disclosure_required: true,
        ai_disclosure_phrase: "Hi, this is the AI receptionist for Northeast Denture Clinic. I can book, reschedule, or take a message. How can I help today?",
        last_reviewed_at: "2026-04-01T00:00:00Z"
      },
      voice: {
        assistant_name: "Dental AI",
        provider_title: "Denturist",
        reason_question: "What brings you in?",
        language: "en-US"
      }
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
          body: "# Denture FAQ\n\nMarket Mall variant — same denture FAQ topics, slightly different aftercare instructions for partials.\n\n## What are partial dentures?\nPartial dentures replace one or more missing teeth when some natural teeth remain. They attach to the remaining teeth with clasps or precision attachments and restore chewing function and appearance.\n\n## How do I care for partial dentures?\nRemove and rinse after eating. Brush daily with a soft-bristled brush. Soak overnight in a denture cleaning solution. Handle carefully to avoid bending clasps.\n\n## When should I schedule a reline?\nA reline is typically recommended every two to three years, or sooner if the fit becomes loose. The denturist evaluates tissue changes at each recall appointment."
        },
        {
          filename: "practice_info.md",
          title: "Practice Info",
          last_updated: "2026-04-15",
          word_count: 740,
          body: "# Practice Info\n\nMarket Mall location, parking inside the mall, mall-hour overlaps, and accepted insurance.\n\n## Location\nMarket Mall Denture Clinic is located inside Market Mall, accessible from the main entrance on the second level near the food court. Free covered parking is available in the mall parkade.\n\n## Mall Hours\nClinic hours align with standard mall operating hours on weekdays. The clinic is closed on weekends. Patients should enter through the main mall entrance during regular mall hours.\n\n## Accepted Insurance\nWe accept most major dental insurance plans including Alberta Blue Cross, Sun Life, and Manulife. Patients should bring their insurance card to every visit."
        }
      ],
      disclosure: {
        ai_disclosure_required: true,
        ai_disclosure_phrase: "Hi, this is the AI receptionist for Market Mall Denture Clinic. I can book, reschedule, or take a message. How may I help?",
        last_reviewed_at: "2026-04-01T00:00:00Z"
      },
      voice: {
        assistant_name: "Dental AI",
        provider_title: "Denturist",
        reason_question: "What brings you in?",
        language: "en-US"
      }
    }
  };
})();
