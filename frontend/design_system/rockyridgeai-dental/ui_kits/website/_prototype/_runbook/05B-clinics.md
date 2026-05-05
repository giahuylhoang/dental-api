# Task 05B — data/clinics.js rewrite

Replace the kit's demo `default` clinic with the user's two real clinics.

## Output

Rewrite exactly one file: `data/clinics.js`.

## Allow-list

`^data/clinics\.js$`

## Goal

After this task, `window.CLINICS` exposes a 2-element array — one entry per clinic the owner manages. Other seed files (users, ai_config) reference these ids.

## File shape (write the file in this exact form, IIFE-wrapped, populating `window.CLINICS`)

```js
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
```

## Verbatim required

- `northeast-denture-clinic`
- `market-mall-denture`
- `Northeast Denture Clinic`
- `Market Mall Denture Clinic`
- `America/Edmonton`
- `+15879738089`
- `+13682990959`
- `5340 Centre St NE`
- `3625 Shaganappi Trail NW`
- `window.CLINICS`

## Forbidden

- The string `"default"` (the old demo clinic id) anywhere.
- The string `"rockyridge-dental"` as a clinic name.
- Adding clinics beyond the two listed above.

## Success criteria

- File size between 600 B and 4 KB.
- Two `id: "..."` lines in the array.
- File is valid JavaScript (the IIFE form above).
- `window.CLINICS` is an array of length 2.

## Constraints

- Keep the existing comment header style (the `// data/clinics.js — populated for…` line + the `// Spelled to match database/models.py canonical enums.` line).
- Match the existing field order: `id, name, display_name, timezone, working_hour_start, working_hour_end, address, contact_phone, booking_notification_email`.
- Phone numbers in E.164 (`+1...`).
