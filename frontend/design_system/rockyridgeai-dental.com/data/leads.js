// data/leads.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.LEADS = [
    { id: "L-001", first: "Jordan",  last: "Mercer",   phone: "+17804410001", email: "jordan.mercer@email.com",   source: "Google",    status: "NEW",       notes: "Interested in full denture consult.",          owner_id: "U-001", clinic_id: "default" },
    { id: "L-002", first: "Tanya",   last: "Osei",     phone: "+17804410002", email: "tanya.osei@email.com",      source: "Referral",  status: "CONTACTED", notes: "Referred by Alice Stevens.",                   owner_id: "U-001", clinic_id: "default" },
    { id: "L-003", first: "Kevin",   last: "Huang",    phone: "+17804410003", email: "kevin.huang@email.com",     source: "Instagram", status: "QUALIFIED", notes: "Wants implant-retained denture quote.",        owner_id: "U-002", clinic_id: "default" },
    { id: "L-004", first: "Miriam",  last: "Fontaine", phone: "+17804410004", email: "miriam.fontaine@email.com", source: "Walk-in",   status: "CONVERTED", notes: "Converted — booked as P-018700.",              owner_id: "U-001", clinic_id: "default" },
    { id: "L-005", first: "Raj",     last: "Patel",    phone: "+17804410005", email: "raj.patel@email.com",       source: "Google",    status: "LOST",      notes: "Chose another clinic.",                        owner_id: "U-002", clinic_id: "default" },
    { id: "L-006", first: "Chloe",   last: "Bergeron", phone: "+17804410006", email: "chloe.bergeron@email.com",  source: "Referral",  status: "NEW",       notes: "Needs partial denture assessment.",            owner_id: "U-001", clinic_id: "default" },
    { id: "L-007", first: "Dmitri",  last: "Volkov",   phone: "+17804410007", email: "dmitri.volkov@email.com",   source: "Other",     status: "CONTACTED", notes: "Called back — left voicemail.",                owner_id: "U-002", clinic_id: "default" },
    { id: "L-008", first: "Amara",   last: "Diallo",   phone: "+17804410008", email: "amara.diallo@email.com",    source: "Google",    status: "QUALIFIED", notes: "Budget confirmed. Scheduling consult.",        owner_id: "U-001", clinic_id: "default" },
    { id: "L-009", first: "Lena",    last: "Schulz",   phone: "+17804410009", email: "lena.schulz@email.com",     source: "Instagram", status: "NEW",       notes: "Saw social post about same-day dentures.",     owner_id: "U-002", clinic_id: "default" },
    { id: "L-010", first: "Patrick", last: "Nwosu",    phone: "+17804410010", email: "patrick.nwosu@email.com",   source: "Walk-in",   status: "CONTACTED", notes: "Walked in asking about pricing.",              owner_id: "U-001", clinic_id: "default" },
  ];
})();
