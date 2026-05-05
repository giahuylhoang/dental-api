# Task 05C — data/users.js rewrite

Add the owner persona (Gia Huy) plus per-clinic front-desk users. Every row gains an `assigned_clinic_ids` array so the multi-clinic switcher can decide which clinics a given user can see.

## Output

Rewrite exactly one file: `data/users.js`.

## Allow-list

`^data/users\.js$`

## Goal

`window.USERS[0]` is the owner with access to both clinics. `lib/auth.js` will read `assigned_clinic_ids` into the session so the sidebar switcher can populate.

## File shape

```js
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
```

## Verbatim required

- `Gia Huy`
- `giahuy.l.hoang@gmail.com`
- `Owner`
- `Front-desk`
- `assigned_clinic_ids`
- `northeast-denture-clinic`
- `market-mall-denture`
- `window.USERS`
- `Northeast Front Desk`
- `Market Mall Front Desk`

## Forbidden

- The clinic id `"default"`.
- The email `"demo@rockyridge.dental"` (the old demo seed).
- Removing the IIFE wrapper.

## Success criteria

- File size between 600 B and 4 KB.
- `assigned_clinic_ids` appears on every user row (3 occurrences total).
- Owner is the first user (`U-100`) with role `Owner`.

## Constraints

- Keep the existing comment header.
- Match the existing field order: `id, clinic_id, [assigned_clinic_ids,] email, full_name, role, is_active`.
- Owner's `clinic_id` (single) is `northeast-denture-clinic` — the default landing clinic. The `assigned_clinic_ids` array is what gates the switcher.
