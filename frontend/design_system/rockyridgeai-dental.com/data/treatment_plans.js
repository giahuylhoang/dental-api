// data/treatment_plans.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.TREATMENT_PLANS = [
    {
      id: "TP-001", patient_id: "P-018342", status: "completed",
      total_estimate: 1480.00, insurance_estimate: 1000.00, patient_estimate: 480.00,
      presented_at: "2026-03-10T10:00:00", accepted_at: "2026-03-10T10:30:00",
      items: [
        { sequence: 1, procedure_code: "23311", description: "Recall exam", fee: 80.00,  insurance_coverage_pct: 100, tooth_number: null, completed_at: "2026-04-21T09:00:00" },
        { sequence: 2, procedure_code: "11101", description: "Composite MOD #14", fee: 220.00, insurance_coverage_pct: 80, tooth_number: 14, completed_at: "2026-04-21T09:30:00" },
        { sequence: 3, procedure_code: "27201", description: "Crown prep #36", fee: 1180.00, insurance_coverage_pct: 50, tooth_number: 36, completed_at: "2026-04-30T09:00:00" },
      ]
    },
    {
      id: "TP-002", patient_id: "P-018501", status: "in_progress",
      total_estimate: 2400.00, insurance_estimate: 1200.00, patient_estimate: 1200.00,
      presented_at: "2026-04-01T11:00:00", accepted_at: "2026-04-01T11:30:00",
      items: [
        { sequence: 1, procedure_code: "27201", description: "Crown prep #36", fee: 1180.00, insurance_coverage_pct: 50, tooth_number: 36, completed_at: "2026-04-02T09:00:00" },
        { sequence: 2, procedure_code: "27202", description: "Crown seat #36", fee: 1220.00, insurance_coverage_pct: 50, tooth_number: 36, completed_at: null },
      ]
    },
    {
      id: "TP-003", patient_id: "P-018611", status: "accepted",
      total_estimate: 4800.00, insurance_estimate: 0, patient_estimate: 4800.00,
      presented_at: "2026-04-30T14:00:00", accepted_at: "2026-04-30T14:45:00",
      items: [
        { sequence: 1, procedure_code: "71201", description: "Implant placement #46", fee: 2400.00, insurance_coverage_pct: 0, tooth_number: 46, completed_at: null },
        { sequence: 2, procedure_code: "71202", description: "Implant crown #46",     fee: 2400.00, insurance_coverage_pct: 0, tooth_number: 46, completed_at: null },
      ]
    },
    {
      id: "TP-004", patient_id: "P-017901", status: "presented",
      total_estimate: 220.00, insurance_estimate: 176.00, patient_estimate: 44.00,
      presented_at: "2026-04-12T10:00:00", accepted_at: null,
      items: [
        { sequence: 1, procedure_code: "11301", description: "Scaling — full mouth", fee: 220.00, insurance_coverage_pct: 80, tooth_number: null, completed_at: null },
      ]
    },
    {
      id: "TP-005", patient_id: "P-018298", status: "draft",
      total_estimate: 1650.00, insurance_estimate: 825.00, patient_estimate: 825.00,
      presented_at: null, accepted_at: null,
      items: [
        { sequence: 1, procedure_code: "51101", description: "Upper complete denture", fee: 1650.00, insurance_coverage_pct: 50, tooth_number: null, completed_at: null },
      ]
    },
    {
      id: "TP-006", patient_id: "P-016102", status: "declined",
      total_estimate: 3200.00, insurance_estimate: 0, patient_estimate: 3200.00,
      presented_at: "2026-04-30T15:00:00", accepted_at: null,
      items: [
        { sequence: 1, procedure_code: "71201", description: "Implant placement #36", fee: 2400.00, insurance_coverage_pct: 0, tooth_number: 36, completed_at: null },
        { sequence: 2, procedure_code: "71202", description: "Implant crown #36",     fee: 800.00,  insurance_coverage_pct: 0, tooth_number: 36, completed_at: null },
      ]
    },
  ];
})();
