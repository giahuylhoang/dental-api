// data/recalls.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.RECALLS = [
    { id: "RCL-001", patient_id: "P-018342", rule_id: "RULE-6MO", due_at: "2026-10-21T00:00:00", sent_at: null,                    status: "pending",   channel: "sms"   },
    { id: "RCL-002", patient_id: "P-018298", rule_id: "RULE-6MO", due_at: "2026-06-08T00:00:00", sent_at: "2026-04-25T09:00:00",   status: "sent",      channel: "email" },
    { id: "RCL-003", patient_id: "P-018501", rule_id: "RULE-6MO", due_at: "2026-10-30T00:00:00", sent_at: null,                    status: "pending",   channel: "sms"   },
    { id: "RCL-004", patient_id: "P-017901", rule_id: "RULE-6MO", due_at: "2026-08-12T00:00:00", sent_at: null,                    status: "pending",   channel: "both"  },
    { id: "RCL-005", patient_id: "P-018611", rule_id: "RULE-1YR", due_at: "2026-04-02T00:00:00", sent_at: "2026-03-20T09:00:00",   status: "completed", channel: "email" },
    { id: "RCL-006", patient_id: "P-016102", rule_id: "RULE-6MO", due_at: "2025-04-30T00:00:00", sent_at: "2025-04-01T09:00:00",   status: "cancelled", channel: "sms"   },
  ];
})();
