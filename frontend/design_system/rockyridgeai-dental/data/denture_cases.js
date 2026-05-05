// data/denture_cases.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.DENTURE_CASES = [
    {
      id: "DC-001", patient_id: "P-018298", arch: "upper", case_type: "complete",
      current_stage: "wax_try_in", status: "open",
      opened_at: "2026-03-01T09:00:00", closed_at: null,
      notes: "Patient has full upper edentulous arch. Wax try-in completed; awaiting final delivery."
    },
    {
      id: "DC-002", patient_id: "P-017901", arch: "lower", case_type: "partial",
      current_stage: "framework_try_in", status: "open",
      opened_at: "2026-04-01T09:00:00", closed_at: null,
      notes: "Kennedy Class II partial lower. Framework sent to lab."
    },
    {
      id: "DC-003", patient_id: "P-018611", arch: "both", case_type: "implant_retained",
      current_stage: "implant_integration", status: "open",
      opened_at: "2026-04-30T10:00:00", closed_at: null,
      notes: "Implant-retained overdenture. Awaiting osseointegration before bar fabrication."
    },
    {
      id: "DC-004", patient_id: "P-016102", arch: "upper", case_type: "immediate",
      current_stage: "delivered", status: "closed",
      opened_at: "2025-09-01T09:00:00", closed_at: "2025-12-15T10:00:00",
      notes: "Immediate upper denture delivered post-extraction. Case closed."
    },
  ];
})();
