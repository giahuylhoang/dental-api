// data/threads.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.THREADS = [
    {
      thread_key: "THR-001", patient_id: "P-018342", channel: "sms", unread: 2,
      last_at: "2026-04-30T09:15:00", subject: "Appointment reminder",
      messages: [
        { id: "MSG-001-1", direction: "out", body: "Hi Alice, your appointment is tomorrow at 8:30 AM. Reply YES to confirm.", sent_at: "2026-04-29T10:00:00", read_at: "2026-04-29T10:05:00" },
        { id: "MSG-001-2", direction: "in",  body: "YES, confirmed. Thank you!", sent_at: "2026-04-29T10:12:00", read_at: null },
        { id: "MSG-001-3", direction: "in",  body: "Can I come 10 minutes early?", sent_at: "2026-04-30T09:15:00", read_at: null },
      ]
    },
    {
      thread_key: "THR-002", patient_id: "P-018298", channel: "email", unread: 0,
      last_at: "2026-04-28T14:30:00", subject: "Recall notice — 6-month checkup",
      messages: [
        { id: "MSG-002-1", direction: "out", body: "Dear Marcus, you are due for your 6-month recall. Please call us to book.", sent_at: "2026-04-25T09:00:00", read_at: "2026-04-25T11:00:00" },
        { id: "MSG-002-2", direction: "in",  body: "Thanks, I will call Monday.", sent_at: "2026-04-28T14:30:00", read_at: "2026-04-28T15:00:00" },
      ]
    },
    {
      thread_key: "THR-003", patient_id: "P-018501", channel: "sms", unread: 1,
      last_at: "2026-04-30T16:45:00", subject: "Crown seat confirmation",
      messages: [
        { id: "MSG-003-1", direction: "out", body: "Priya, your crown seat is scheduled for today at 3:30 PM.", sent_at: "2026-04-30T08:00:00", read_at: "2026-04-30T08:30:00" },
        { id: "MSG-003-2", direction: "in",  body: "Running 5 minutes late, sorry!", sent_at: "2026-04-30T16:45:00", read_at: null },
      ]
    },
    {
      thread_key: "THR-004", patient_id: "P-017901", channel: "whatsapp", unread: 0,
      last_at: "2026-04-22T11:00:00", subject: "Treatment plan questions",
      messages: [
        { id: "MSG-004-1", direction: "in",  body: "Hi, I had a question about the treatment plan cost.", sent_at: "2026-04-22T10:45:00", read_at: "2026-04-22T10:50:00" },
        { id: "MSG-004-2", direction: "out", body: "Hi Eli, happy to help. Your insurance covers 80% of the scaling. Your portion is $44.", sent_at: "2026-04-22T11:00:00", read_at: "2026-04-22T11:05:00" },
      ]
    },
    {
      thread_key: "THR-005", patient_id: "P-018611", channel: "email", unread: 3,
      last_at: "2026-05-01T08:20:00", subject: "Implant follow-up instructions",
      messages: [
        { id: "MSG-005-1", direction: "out", body: "Sofia, please find attached your post-implant care instructions.", sent_at: "2026-04-30T17:00:00", read_at: null },
        { id: "MSG-005-2", direction: "in",  body: "Thank you. I have some swelling — is that normal?", sent_at: "2026-05-01T07:00:00", read_at: null },
        { id: "MSG-005-3", direction: "in",  body: "Also, can I eat soft foods?", sent_at: "2026-05-01T07:05:00", read_at: null },
        { id: "MSG-005-4", direction: "in",  body: "Please call me when you can.", sent_at: "2026-05-01T08:20:00", read_at: null },
      ]
    },
    {
      thread_key: "THR-006", patient_id: "P-016102", channel: "sms", unread: 0,
      last_at: "2026-04-15T13:00:00", subject: "New patient consult reminder",
      messages: [
        { id: "MSG-006-1", direction: "out", body: "Daniel, your new patient consult is April 30 at 2:30 PM.", sent_at: "2026-04-15T13:00:00", read_at: "2026-04-15T14:00:00" },
      ]
    },
    {
      thread_key: "THR-007", patient_id: "P-018342", channel: "email", unread: 0,
      last_at: "2026-04-10T09:00:00", subject: "Invoice INV-2026-0871 receipt",
      messages: [
        { id: "MSG-007-1", direction: "out", body: "Hi Alice, your invoice INV-2026-0871 for $480.00 has been paid. Thank you.", sent_at: "2026-04-10T09:00:00", read_at: "2026-04-10T09:30:00" },
      ]
    },
    {
      thread_key: "THR-008", patient_id: "P-018501", channel: "whatsapp", unread: 1,
      last_at: "2026-04-29T18:00:00", subject: "Lab case update",
      messages: [
        { id: "MSG-008-1", direction: "out", body: "Priya, your crown has arrived from the lab. We will seat it at your appointment tomorrow.", sent_at: "2026-04-29T18:00:00", read_at: null },
      ]
    },
  ];
})();
