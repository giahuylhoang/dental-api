# Task 06C — admin_mock.js refactor (keyed by clinic_id)

Refactor `data/admin_mock.js` from flat single-clinic to keyed by clinic_id, with both clinics populated and ROUTING/GREETING proxied into `window.AI_CONFIG` so there's one source of truth. Also add `disclosure` and `voice` blocks to `data/ai_config.js` (additive, both clinics).

## Output

Modify exactly two files:
- `data/admin_mock.js` (full rewrite of the IIFE shape; data inside preserved/extended)
- `data/ai_config.js` (additive — append `disclosure` + `voice` keys to each clinic block)

## Allow-list

`^data/(admin_mock|ai_config)\.js$`

## Goal

After this task:
- `window.ADMIN_MOCK.CLINICS` is an object keyed by clinic_id.
- `window.ADMIN_MOCK.getClinic()` returns the merged record (CLINIC + KPIS + CALLS + TRANSCRIPTS + PATIENTS + APPOINTMENTS + ROUTING + GREETING) for the current clinic.
- `window.ADMIN_MOCK.setCurrentClinic(id)` mutates state, calls `RRD.setCurrentClinic`, dispatches `clinic-changed`.
- Legacy getters (`window.ADMIN_MOCK.CLINIC`, `.KPIS`, `.CALLS`, `.TRANSCRIPTS`, `.PATIENTS`, `.APPOINTMENTS`, `.ROUTING`, `.GREETING`) still work, proxying to the current clinic.
- `window.AI_CONFIG[clinicId].disclosure` exists for both clinics: `{ ai_disclosure_required, ai_disclosure_phrase, last_reviewed_at }`.
- `window.AI_CONFIG[clinicId].voice` exists for both clinics: `{ assistant_name, provider_title, reason_question, language }`.

## File 1 — `data/admin_mock.js` (rewrite)

The current file has a single flat `window.ADMIN_MOCK = { CLINIC, ROUTING, GREETING, KPIS, CALLS, TRANSCRIPTS, PATIENTS, APPOINTMENTS }`. Restructure to:

```js
// data/admin_mock.js — operational dataset for the dark _prototype admin.
// Plan v3: keyed by clinic_id; ROUTING/GREETING delegate to window.AI_CONFIG
// (single source of truth). Both clinics populated with deliberately
// different counts so the clinic switcher demo is visibly real.

window.ADMIN_MOCK = (function () {
  // ... helpers (daysAgo, iso, todayAt, isAfterHours) ...

  function buildClinic(id, opts) {
    var CLINIC = {
      slug: id,
      name: opts.name,
      timezone: opts.tz,
      avg_case_value_cents: opts.acv,
      front_desk_hourly_cost_cents: 2500,
    };
    var KPIS = computeKpis(opts.calls, opts.appointments, CLINIC);
    return {
      CLINIC,
      KPIS,
      CALLS: opts.calls,
      TRANSCRIPTS: opts.transcripts,
      PATIENTS: opts.patients,
      APPOINTMENTS: opts.appointments,
    };
  }

  // Northeast: keep existing scale (12 patients, 32 calls, 14 appts).
  var NE_OPTS = { name: 'Northeast Denture Clinic', tz: 'America/Edmonton', acv: 65000,
                  calls: NE_CALLS, transcripts: NE_TRANSCRIPTS,
                  patients: NE_PATIENTS, appointments: NE_APPOINTMENTS };

  // Market Mall: deliberately different so switching is visible.
  // 7 patients, 18 calls (10 booked / 4 transferred / 2 voicemail / 2 missed),
  // 9 appts today.
  var MM_OPTS = { name: 'Market Mall Denture Clinic', tz: 'America/Edmonton', acv: 72500,
                  calls: MM_CALLS, transcripts: MM_TRANSCRIPTS,
                  patients: MM_PATIENTS, appointments: MM_APPOINTMENTS };

  var CLINICS = {
    'northeast-denture-clinic': buildClinic('northeast-denture-clinic', NE_OPTS),
    'market-mall-denture':      buildClinic('market-mall-denture',      MM_OPTS),
  };

  var STATE = {
    CURRENT_CLINIC_ID: (window.RRD && window.RRD.getCurrentClinicId && window.RRD.getCurrentClinicId())
                       || Object.keys(CLINICS)[0]
  };

  function getClinic() {
    var c = CLINICS[STATE.CURRENT_CLINIC_ID];
    if (!c) return null;
    var ai = (window.AI_CONFIG && window.AI_CONFIG[STATE.CURRENT_CLINIC_ID]) || {};
    return Object.assign({}, c, {
      ROUTING:  ai.routing  || {},
      GREETING: ai.greeting || {},
    });
  }

  function setCurrentClinic(id) {
    if (!CLINICS[id]) return false;
    STATE.CURRENT_CLINIC_ID = id;
    if (window.RRD && window.RRD.setCurrentClinic) {
      window.RRD.setCurrentClinic(id);
    }
    try {
      window.dispatchEvent(new CustomEvent('clinic-changed', { detail: { id: id } }));
    } catch (_) { /* no-op */ }
    return true;
  }

  return Object.assign(STATE, {
    CLINICS: CLINICS,
    getClinic: getClinic,
    setCurrentClinic: setCurrentClinic,
    get CLINIC()       { return (getClinic() || {}).CLINIC; },
    get KPIS()         { return (getClinic() || {}).KPIS; },
    get CALLS()        { return (getClinic() || {}).CALLS; },
    get TRANSCRIPTS()  { return (getClinic() || {}).TRANSCRIPTS; },
    get PATIENTS()     { return (getClinic() || {}).PATIENTS; },
    get APPOINTMENTS() { return (getClinic() || {}).APPOINTMENTS; },
    get ROUTING()      { return (getClinic() || {}).ROUTING; },
    get GREETING()     { return (getClinic() || {}).GREETING; },
  });
})();
```

**Northeast Denture Clinic** keeps the existing data (12 patients, 32 calls, 14 appointments). Preserve the existing helper functions (`daysAgo`, `iso`, `todayAt`, `isAfterHours`, `computeKpis`) and the existing patient/call/transcript/appointment definitions — just move them inside the IIFE, name them `NE_PATIENTS` / `NE_CALLS` / `NE_TRANSCRIPTS` / `NE_APPOINTMENTS`.

**Market Mall Denture Clinic** is a new dataset:
- 7 patients (different first/last names, different phones in `+1403*` range, mix of `lead_status` values)
- 18 calls (10 outcome=booked, 4 transferred, 2 voicemail, 2 missed) over the past 14 days
- 9 appointments today across providers (Dr. Tran / Dr. Singh / Hygienist Maya), 6 booked-by-AI / 3 booked-by-front-desk
- 2 transcripts (one short, one medium)

Keep the data realistic — phone numbers in E.164, ISO timestamps, realistic `last_contact_at` values. The point is that the dashboard KPIs visibly differ from Northeast.

## File 2 — `data/ai_config.js` (additive)

For each clinic block, append two new top-level keys after `knowledge_docs`:

```js
disclosure: {
  ai_disclosure_required: true,
  ai_disclosure_phrase: "Hi, this is the AI receptionist for {clinic.name}. I can book, reschedule, or take a message. How can I help today?",
  last_reviewed_at: "2026-04-01T00:00:00Z"
},
voice: {
  assistant_name: "Dental AI",
  provider_title: "Denturist",
  reason_question: "What brings you in?",
  language: "en-US"
}
```

For Market Mall use `provider_title: "Denturist"`, same `assistant_name: "Dental AI"`, `language: "en-US"`. The `ai_disclosure_phrase` may differ between clinics — Northeast can use the default above; Market Mall can use a slightly different variant for demo realism.

## Verbatim required (across both files)

- `window.ADMIN_MOCK`
- `CLINICS`
- `northeast-denture-clinic`
- `market-mall-denture`
- `Northeast Denture Clinic`
- `Market Mall Denture Clinic`
- `setCurrentClinic`
- `clinic-changed`
- `getClinic`
- `disclosure`
- `voice`
- `ai_disclosure_required`
- `ai_disclosure_phrase`
- `assistant_name`
- `provider_title`
- `reason_question`
- `Denturist`
- `Dental AI`

## Success criteria

- `data/admin_mock.js` size 22–80 KB.
- `data/ai_config.js` size 5–24 KB (after additive `disclosure`+`voice`).
- `assert_grep_count "buildClinic\(" 1 4` in admin_mock.js.
- Both clinic ids present as keys in `CLINICS`.
- AI_CONFIG has `disclosure:` and `voice:` blocks twice (one per clinic).
- Loading both files in Node with a stubbed `window` shim succeeds and `window.ADMIN_MOCK.CLINICS` has length 2.

## Constraints

- Keep existing transcripts, patient names, appointment shapes byte-identical for Northeast — no churn there. Just move them inside the IIFE and rename the bindings.
- All new Market Mall data must be realistic (real-looking names, valid E.164 phones, ISO timestamps).
