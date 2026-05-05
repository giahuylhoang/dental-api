// data/clinics.js — populated for the rockyridgeai-dental.com static prototype.
// Spelled to match database/models.py canonical enums.
(function () {
  window.CLINICS = [
    {
      id: "northeast-denture-clinic",
      name: "northeast-denture-clinic",
      display_name: "Northeast Denture Clinic",
      timezone: "America/Edmonton",
      working_hour_start: "09:00",
      working_hour_end: "17:00",
      address: "5340 Centre St NE, Calgary, AB T2K 4R5",
      contact_phone: "+15879738089",
      booking_notification_email: "front@northeast-denture.ca"
    },
    {
      id: "market-mall-denture",
      name: "market-mall-denture",
      display_name: "Market Mall Denture Clinic",
      timezone: "America/Edmonton",
      working_hour_start: "09:00",
      working_hour_end: "17:00",
      address: "3625 Shaganappi Trail NW, Calgary, AB T3A 0E2",
      contact_phone: "+13682990959",
      booking_notification_email: "front@marketmall-denture.ca"
    }
  ];
})();
