// data/users.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.USERS = [
    {
      id: "U-100",
      clinic_id: "northeast-denture-clinic",
      assigned_clinic_ids: ["northeast-denture-clinic", "market-mall-denture"],
      email: "giahuy.l.hoang@gmail.com",
      full_name: "Gia Huy",
      role: "Owner",
      is_active: true
    },
    {
      id: "U-101",
      clinic_id: "northeast-denture-clinic",
      assigned_clinic_ids: ["northeast-denture-clinic"],
      email: "front@northeast-denture.ca",
      full_name: "Northeast Front Desk",
      role: "Front-desk",
      is_active: true
    },
    {
      id: "U-102",
      clinic_id: "market-mall-denture",
      assigned_clinic_ids: ["market-mall-denture"],
      email: "front@marketmall-denture.ca",
      full_name: "Market Mall Front Desk",
      role: "Front-desk",
      is_active: true
    }
  ];
})();
