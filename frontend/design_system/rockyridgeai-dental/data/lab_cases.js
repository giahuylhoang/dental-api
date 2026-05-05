// data/lab_cases.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.LAB_CASES = [
    {
      id: "LC-2026-0001", denture_case_id: "DC-001", vendor_id: "V-01", vendor_name: "Precision Dental Lab",
      case_number: "PDL-8821", sent_at: "2026-04-10T08:00:00", due_back_at: "2026-04-17T17:00:00",
      returned_at: "2026-04-17T14:30:00", status: "returned", lab_fee: 380.00,
      courier_tracking: "1Z999AA10123456784",
      events: [
        { kind: "sent",     occurred_at: "2026-04-10T08:00:00", payload: { notes: "Upper complete denture wax try-in" } },
        { kind: "returned", occurred_at: "2026-04-17T14:30:00", payload: { notes: "Ready for try-in appointment" } },
      ]
    },
    {
      id: "LC-2026-0002", denture_case_id: "DC-002", vendor_id: "V-01", vendor_name: "Precision Dental Lab",
      case_number: "PDL-8845", sent_at: "2026-04-22T08:00:00", due_back_at: "2026-04-29T17:00:00",
      returned_at: null, status: "in_progress", lab_fee: 420.00,
      courier_tracking: "1Z999AA10123456785",
      events: [
        { kind: "sent",       occurred_at: "2026-04-22T08:00:00", payload: { notes: "Lower partial framework" } },
        { kind: "in_progress", occurred_at: "2026-04-23T09:00:00", payload: { notes: "Lab confirmed receipt" } },
      ]
    },
    {
      id: "LC-2026-0003", denture_case_id: null, vendor_id: "V-02", vendor_name: "Crown Craft Lab",
      case_number: "CCL-3301", sent_at: "2026-04-25T08:00:00", due_back_at: "2026-04-30T17:00:00",
      returned_at: "2026-04-30T10:00:00", status: "returned", lab_fee: 295.00,
      courier_tracking: "1Z999AA10123456786",
      events: [
        { kind: "sent",     occurred_at: "2026-04-25T08:00:00", payload: { notes: "PFM crown #36 for Priya Khanna" } },
        { kind: "returned", occurred_at: "2026-04-30T10:00:00", payload: { notes: "Crown seated successfully" } },
      ]
    },
    {
      id: "LC-2026-0004", denture_case_id: "DC-003", vendor_id: "V-01", vendor_name: "Precision Dental Lab",
      case_number: "PDL-8860", sent_at: "2026-04-28T08:00:00", due_back_at: "2026-05-05T17:00:00",
      returned_at: null, status: "sent", lab_fee: 510.00,
      courier_tracking: "1Z999AA10123456787",
      events: [
        { kind: "sent", occurred_at: "2026-04-28T08:00:00", payload: { notes: "Implant-retained overdenture bar" } },
      ]
    },
    {
      id: "LC-2026-0005", denture_case_id: "DC-004", vendor_id: "V-03", vendor_name: "Alberta Denture Works",
      case_number: "ADW-0091", sent_at: null, due_back_at: null,
      returned_at: null, status: "draft", lab_fee: 0,
      courier_tracking: null,
      events: []
    },
    {
      id: "LC-2026-0006", denture_case_id: "DC-001", vendor_id: "V-01", vendor_name: "Precision Dental Lab",
      case_number: "PDL-8799", sent_at: "2026-03-01T08:00:00", due_back_at: "2026-03-08T17:00:00",
      returned_at: "2026-03-10T11:00:00", status: "remake", lab_fee: 380.00,
      courier_tracking: "1Z999AA10123456780",
      events: [
        { kind: "sent",   occurred_at: "2026-03-01T08:00:00", payload: { notes: "Initial wax try-in" } },
        { kind: "remake", occurred_at: "2026-03-10T11:00:00", payload: { notes: "Occlusion adjustment required — remake requested" } },
      ]
    },
    {
      id: "LC-2026-0007", denture_case_id: null, vendor_id: "V-02", vendor_name: "Crown Craft Lab",
      case_number: "CCL-3288", sent_at: "2026-04-01T08:00:00", due_back_at: "2026-04-08T17:00:00",
      returned_at: "2026-04-08T09:00:00", status: "returned", lab_fee: 260.00,
      courier_tracking: "1Z999AA10123456781",
      events: [
        { kind: "sent",     occurred_at: "2026-04-01T08:00:00", payload: { notes: "Zirconia crown #14" } },
        { kind: "returned", occurred_at: "2026-04-08T09:00:00", payload: {} },
      ]
    },
    {
      id: "LC-2026-0008", denture_case_id: "DC-002", vendor_id: "V-03", vendor_name: "Alberta Denture Works",
      case_number: "ADW-0088", sent_at: "2026-02-10T08:00:00", due_back_at: "2026-02-20T17:00:00",
      returned_at: null, status: "cancelled", lab_fee: 0,
      courier_tracking: null,
      events: [
        { kind: "sent",      occurred_at: "2026-02-10T08:00:00", payload: { notes: "Partial framework" } },
        { kind: "cancelled", occurred_at: "2026-02-12T10:00:00", payload: { notes: "Patient cancelled treatment" } },
      ]
    },
  ];
})();
