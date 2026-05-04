// data/claims.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.CLAIMS = [
    {
      id: "CLM-2026-0001", invoice_id: "INV-2026-0871", carrier: "Alberta Blue Cross",
      kind: "claim", status: "paid", assignment_of_benefits: true,
      submitted_at: "2026-04-05T10:00:00", adjudicated_at: "2026-04-09T14:00:00",
      accepted_amount: 480.00,
      response_codes: [{ code: "00", description: "Claim processed", severity: "info" }]
    },
    {
      id: "CLM-2026-0002", invoice_id: "INV-2026-0870", carrier: "Manulife",
      kind: "claim", status: "partial", assignment_of_benefits: true,
      submitted_at: "2026-04-20T09:00:00", adjudicated_at: "2026-04-25T11:00:00",
      accepted_amount: 620.00,
      response_codes: [
        { code: "00", description: "Claim processed", severity: "info" },
        { code: "W14", description: "Benefit maximum reached for crown", severity: "warning" }
      ]
    },
    {
      id: "CLM-2026-0003", invoice_id: "INV-2026-0869", carrier: "Alberta Health",
      kind: "predetermination", status: "submitted", assignment_of_benefits: false,
      submitted_at: "2026-04-28T08:30:00", adjudicated_at: null,
      accepted_amount: null,
      response_codes: []
    },
    {
      id: "CLM-2026-0004", invoice_id: "INV-2026-0868", carrier: "Sun Life",
      kind: "claim", status: "adjudicated", assignment_of_benefits: true,
      submitted_at: "2026-04-01T10:00:00", adjudicated_at: "2026-04-07T09:00:00",
      accepted_amount: 220.00,
      response_codes: [{ code: "00", description: "Claim processed", severity: "info" }]
    },
    {
      id: "CLM-2026-0005", invoice_id: "INV-2026-0872", carrier: "Canada Life",
      kind: "claim", status: "rejected", assignment_of_benefits: true,
      submitted_at: "2026-03-15T10:00:00", adjudicated_at: "2026-03-20T14:00:00",
      accepted_amount: 0,
      response_codes: [
        { code: "E01", description: "Patient not eligible on date of service", severity: "error" }
      ]
    },
    {
      id: "CLM-2026-0006", invoice_id: "INV-2026-0873", carrier: "Pacific Blue Cross",
      kind: "claim", status: "draft", assignment_of_benefits: true,
      submitted_at: null, adjudicated_at: null,
      accepted_amount: null,
      response_codes: []
    },
  ];
})();
