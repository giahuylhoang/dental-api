// data/waitlist.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.WAITLIST = [
    { id: "WL-001", patient_id: "P-018298", requested_window_start: "2026-05-01T08:00:00", requested_window_end: "2026-05-01T12:00:00", provider_pref: "PRV-002", service_id: "SVC-006", priority: 1, status: "open"      },
    { id: "WL-002", patient_id: "P-017901", requested_window_start: "2026-05-05T09:00:00", requested_window_end: "2026-05-05T17:00:00", provider_pref: "PRV-003", service_id: "SVC-002", priority: 2, status: "filled"     },
    { id: "WL-003", patient_id: "P-016102", requested_window_start: "2026-04-28T08:00:00", requested_window_end: "2026-04-28T17:00:00", provider_pref: null,      service_id: "SVC-008", priority: 3, status: "expired"    },
    { id: "WL-004", patient_id: "P-018611", requested_window_start: "2026-05-10T08:00:00", requested_window_end: "2026-05-10T12:00:00", provider_pref: "PRV-001", service_id: "SVC-007", priority: 1, status: "cancelled"  },
  ];
})();
