// data/audit_log.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.AUDIT_LOG = [
    { id: "AUD-001", user_id: "U-001", action: "read",   entity_type: "Patient",        entity_id: "P-018342", occurred_at: "2026-04-30T08:00:00", ip: "192.168.1.10" },
    { id: "AUD-002", user_id: "U-001", action: "update", entity_type: "Appointment",    entity_id: "A-1",      occurred_at: "2026-04-30T08:05:00", ip: "192.168.1.10" },
    { id: "AUD-003", user_id: "U-002", action: "insert", entity_type: "Invoice",        entity_id: "INV-2026-0871", occurred_at: "2026-04-10T09:00:00", ip: "192.168.1.11" },
    { id: "AUD-004", user_id: "U-003", action: "read",   entity_type: "TreatmentPlan",  entity_id: "TP-002",   occurred_at: "2026-04-30T10:00:00", ip: "192.168.1.12" },
    { id: "AUD-005", user_id: "U-001", action: "update", entity_type: "Lead",           entity_id: "L-003",    occurred_at: "2026-04-29T14:00:00", ip: "192.168.1.10" },
    { id: "AUD-006", user_id: "U-002", action: "export", entity_type: "Patient",        entity_id: "P-018501", occurred_at: "2026-04-28T16:00:00", ip: "192.168.1.11" },
    { id: "AUD-007", user_id: "U-004", action: "insert", entity_type: "Appointment",    entity_id: "A-8",      occurred_at: "2026-04-25T09:30:00", ip: "192.168.1.13" },
    { id: "AUD-008", user_id: "U-001", action: "delete", entity_type: "Recall",         entity_id: "RCL-006",  occurred_at: "2026-04-20T11:00:00", ip: "192.168.1.10" },
    { id: "AUD-009", user_id: "U-003", action: "read",   entity_type: "LabCase",        entity_id: "LC-2026-0003", occurred_at: "2026-04-30T11:00:00", ip: "192.168.1.12" },
    { id: "AUD-010", user_id: "U-002", action: "update", entity_type: "DentureCase",    entity_id: "DC-001",   occurred_at: "2026-04-17T15:00:00", ip: "192.168.1.11" },
    { id: "AUD-011", user_id: "U-001", action: "insert", entity_type: "Claim",          entity_id: "CLM-2026-0006", occurred_at: "2026-04-30T13:00:00", ip: "192.168.1.10" },
    { id: "AUD-012", user_id: "U-004", action: "read",   entity_type: "Thread",         entity_id: "THR-005",  occurred_at: "2026-05-01T09:00:00", ip: "192.168.1.13" },
  ];
})();
