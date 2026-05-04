// data/users.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.USERS = [
    { id: "U-001", clinic_id: "default", email: "demo@rockyridge.dental",    full_name: "Hau Le",        role: "Owner",      is_active: true  },
    { id: "U-002", clinic_id: "default", email: "sara.lim@rockyridge.dental", full_name: "Sara Lim",     role: "Provider",   is_active: true  },
    { id: "U-003", clinic_id: "default", email: "renu.sharma@rockyridge.dental", full_name: "Renu Sharma", role: "Provider", is_active: true  },
    { id: "U-004", clinic_id: "default", email: "front@rockyridge.dental",   full_name: "Jamie Tran",    role: "Front-desk", is_active: true  },
  ];
})();
