// data/services.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.SERVICES = [
    { id: "SVC-001", name: "Recall Exam",              description: "Comprehensive recall examination and charting.",          duration_min: 30,  base_price: 80.00   },
    { id: "SVC-002", name: "Scaling — Full Mouth",     description: "Full-mouth scaling and root planing.",                   duration_min: 60,  base_price: 220.00  },
    { id: "SVC-003", name: "Composite Restoration",    description: "Single-surface composite resin restoration.",            duration_min: 45,  base_price: 180.00  },
    { id: "SVC-004", name: "Crown Preparation",        description: "Preparation and temporisation for a full crown.",        duration_min: 90,  base_price: 1180.00 },
    { id: "SVC-005", name: "Crown Seat",               description: "Cementation of permanent crown.",                       duration_min: 45,  base_price: 1220.00 },
    { id: "SVC-006", name: "Complete Denture — Upper", description: "Fabrication and delivery of upper complete denture.",    duration_min: 60,  base_price: 1650.00 },
    { id: "SVC-007", name: "Implant Placement",        description: "Surgical placement of endosseous implant fixture.",      duration_min: 90,  base_price: 2400.00 },
    { id: "SVC-008", name: "New Patient Consult",      description: "Initial consultation, radiographs, and treatment plan.", duration_min: 60,  base_price: 120.00  },
  ];
})();
