// data/admin_mock.js — operational dataset for the dark _prototype admin.
// Plan v3: keyed by clinic_id; ROUTING/GREETING delegate to window.AI_CONFIG
// (single source of truth). Both clinics populated with deliberately
// different counts so the clinic switcher demo is visibly real.

window.ADMIN_MOCK = (function () {
  // ── helpers ──────────────────────────────────────────────────────────
  var now = new Date();
  var Y = now.getFullYear(), M = now.getMonth(), D = now.getDate();

  function daysAgo(n) { return new Date(Y, M, D - n); }
  function iso(d) { return d.toISOString(); }
  function todayAt(h, m) { return new Date(Y, M, D, h, m, 0); }
  function pad2(n) { return n < 10 ? '0' + n : '' + n; }
  function fmtDate(d) {
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
  }
  function dayAt(daysBack, h, m, s) {
    return new Date(Y, M, D - daysBack, h, m, s || 0);
  }

  function isAfterHoursNE(d) {
    var days = ['sun','mon','tue','wed','thu','fri','sat'];
    var day = days[d.getDay()];
    var hours = {
      mon: { open: '09:00', close: '17:00' },
      tue: { open: '09:00', close: '17:00' },
      wed: { open: '09:00', close: '19:00' },
      thu: { open: '09:00', close: '19:00' },
      fri: { open: '09:00', close: '14:00' },
      sat: { open: '09:00', close: '18:00' },
      sun: { open: null, close: null },
    };
    var h = hours[day];
    if (!h || !h.open) return true;
    var hhmm = pad2(d.getHours()) + ':' + pad2(d.getMinutes());
    return hhmm < h.open || hhmm >= h.close;
  }

  function isAfterHoursMM(d) {
    var days = ['sun','mon','tue','wed','thu','fri','sat'];
    var day = days[d.getDay()];
    var hours = {
      mon: { open: '09:00', close: '17:00' },
      tue: { open: '09:00', close: '17:00' },
      wed: { open: '09:00', close: '17:00' },
      thu: { open: '09:00', close: '17:00' },
      fri: { open: '09:00', close: '17:00' },
      sat: { open: null, close: null },
      sun: { open: null, close: null },
    };
    var h = hours[day];
    if (!h || !h.open) return true;
    var hhmm = pad2(d.getHours()) + ':' + pad2(d.getMinutes());
    return hhmm < h.open || hhmm >= h.close;
  }

  // ── KPI computation ─────────────────────────────────────────────────
  function computeKpis(calls, appointments, clinic) {
    var bookedCalls = calls.filter(function (c) { return c.outcome === 'booked'; });
    var nonMissed = calls.filter(function (c) { return c.outcome !== 'missed'; });
    var agentHandled = calls.filter(function (c) { return c.outcome === 'agent_handled'; });
    var transferred = calls.filter(function (c) { return c.outcome === 'transferred'; });
    var voicemails = calls.filter(function (c) { return c.outcome === 'voicemail'; });
    var bookedAfterHours = bookedCalls.filter(function (c) { return c.after_hours; });
    var totalDurNonMissed = nonMissed.reduce(function (s, c) { return s + c.duration_seconds; }, 0);

    var kpis = {
      period_label: 'This month',
      bookings: { value: bookedCalls.length, delta_pct: 12 },
      revenue_captured_cents: { value: bookedCalls.length * clinic.avg_case_value_cents, delta_pct: 15 },
      after_hours_revenue_cents: { value: bookedAfterHours.length * clinic.avg_case_value_cents, delta_pct: 8 },
      front_desk_hours_saved: { value: Math.round(totalDurNonMissed / 360) / 10, delta_pct: 6 },
      calls_handled: {
        value: nonMissed.length,
        in_hours: nonMissed.filter(function (c) { return !c.after_hours; }).length,
        after_hours: nonMissed.filter(function (c) { return c.after_hours; }).length,
        delta_pct: 10,
      },
      resolution_rate_pct: {
        value: Math.round((bookedCalls.length + agentHandled.length) / (bookedCalls.length + agentHandled.length + transferred.length + voicemails.length) * 100),
        delta_pct: 4,
      },
      missed_call_recovery_pct: {
        value: Math.round(nonMissed.length / calls.length * 100),
        delta_pct: -3,
      },
      avg_response_seconds: { value: 1.4, delta_pct: -8 },
      sparklines: {},
      trend_14d: [],
    };

    var dayBuckets = {};
    for (var i = 0; i < 14; i++) {
      dayBuckets[fmtDate(daysAgo(i))] = { calls: 0, booked: 0, handled: 0, dur: 0 };
    }
    calls.forEach(function (c) {
      var ds = c.started_at.slice(0, 10);
      if (dayBuckets[ds]) {
        dayBuckets[ds].calls++;
        if (c.outcome === 'booked') dayBuckets[ds].booked++;
        if (c.outcome !== 'missed') { dayBuckets[ds].handled++; dayBuckets[ds].dur += c.duration_seconds; }
      }
    });

    var trend14d = [];
    var spBookings = [], spCalls = [], spResolution = [], spMissed = [], spResponse = [];
    var spRevenue = [], spAfterHoursRev = [], spHoursSaved = [];
    for (var j = 13; j >= 0; j--) {
      var ds = fmtDate(daysAgo(j));
      var b = dayBuckets[ds] || { calls: 0, booked: 0, handled: 0, dur: 0 };
      trend14d.push({ date: ds, calls: b.calls, booked: b.booked });
      spBookings.push(b.booked);
      spCalls.push(b.handled);
      spResolution.push(b.calls > 0 ? Math.round(b.handled / b.calls * 100) : 100);
      spMissed.push(b.calls > 0 ? Math.round(b.handled / b.calls * 100) : 100);
      spResponse.push(+(1.2 + Math.random() * 0.5).toFixed(1));
      spRevenue.push(b.booked * clinic.avg_case_value_cents);
      spAfterHoursRev.push(0);
      spHoursSaved.push(Math.round(b.dur / 360) / 10);
    }

    kpis.trend_14d = trend14d;
    kpis.sparklines = {
      bookings: spBookings,
      calls_handled: spCalls,
      resolution_rate_pct: spResolution,
      missed_call_recovery_pct: spMissed,
      avg_response_seconds: spResponse,
      revenue_captured_cents: spRevenue,
      after_hours_revenue_cents: spAfterHoursRev,
      front_desk_hours_saved: spHoursSaved,
    };

    return kpis;
  }

  // ── buildClinic ─────────────────────────────────────────────────────
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
      CLINIC: CLINIC,
      KPIS: KPIS,
      CALLS: opts.calls,
      TRANSCRIPTS: opts.transcripts,
      PATIENTS: opts.patients,
      APPOINTMENTS: opts.appointments,
    };
  }

  // ══════════════════════════════════════════════════════════════════════
  // NORTHEAST DENTURE CLINIC — 12 patients, 32 calls, 14 appointments
  // ══════════════════════════════════════════════════════════════════════

  var NE_PATIENTS = [
    { patient_id: 'pt_a1b2c3', first_name: 'Margaret', last_name: 'Olsen', phone_e164: '+15879731042', email: 'margaret.olsen@telus.net', lead_status: 'booked', tags: ['denture-fitting', 'recall'], last_contact_at: iso(daysAgo(1)), total_calls: 4, notes: 'Upper partial refit scheduled. Patient prefers morning appointments. Insurance through Blue Cross.' },
    { patient_id: 'pt_d4e5f6', first_name: 'Gerald', last_name: 'Fehr', phone_e164: '+17804529917', email: null, lead_status: 'booked', tags: ['recall'], last_contact_at: iso(daysAgo(2)), total_calls: 3, notes: 'Annual recall. No outstanding treatment. Reliable attendee.' },
    { patient_id: 'pt_g7h8i9', first_name: 'Donna', last_name: 'Fong', phone_e164: '+15879734488', email: 'donna.fong@shaw.ca', lead_status: 'new', tags: ['new-patient', 'consult'], last_contact_at: iso(daysAgo(0)), total_calls: 1, notes: 'First-time caller. Referred by Dr. Patel. Interested in implant-supported denture consult.' },
    { patient_id: 'pt_j1k2l3', first_name: 'Robert', last_name: 'Makokis', phone_e164: '+17804553321', email: 'r.makokis@gmail.com', lead_status: 'contacted', tags: ['denture-fitting'], last_contact_at: iso(daysAgo(3)), total_calls: 2, notes: 'Lower complete denture. Waiting on lab work. Follow-up call completed.' },
    { patient_id: 'pt_m4n5o6', first_name: 'Patricia', last_name: 'Savard', phone_e164: '+15879738801', email: 'p.savard@outlook.com', lead_status: 'booked', tags: ['emergency'], last_contact_at: iso(daysAgo(1)), total_calls: 2, notes: 'Fractured lower denture. Emergency repair booked same-day.' },
    { patient_id: 'pt_p7q8r9', first_name: 'Wayne', last_name: 'Chicken', phone_e164: '+17804557762', email: null, lead_status: 'contacted', tags: ['consult'], last_contact_at: iso(daysAgo(5)), total_calls: 3, notes: 'Comparison-shopping for implant consult. Called twice for pricing. Undecided.' },
    { patient_id: 'pt_s1t2u3', first_name: 'Helen', last_name: 'Brandt', phone_e164: '+15879732205', email: 'helen.brandt@telus.net', lead_status: 'completed', tags: ['denture-fitting', 'recall'], last_contact_at: iso(daysAgo(7)), total_calls: 6, notes: 'Upper and lower complete dentures delivered. Final adjustment done. Next recall in 6 months.' },
    { patient_id: 'pt_v4w5x6', first_name: 'Dennis', last_name: 'Favel', phone_e164: '+17804551198', email: null, lead_status: 'new', tags: ['new-patient'], last_contact_at: iso(daysAgo(4)), total_calls: 1, notes: 'Walk-in inquiry converted to phone lead. Needs full assessment.' },
    { patient_id: 'pt_y7z8a1', first_name: 'Lorraine', last_name: 'Flett', phone_e164: '+15879736643', email: 'lorraine.flett@gmail.com', lead_status: 'booked', tags: ['recall'], last_contact_at: iso(daysAgo(0)), total_calls: 2, notes: 'Recall and hygiene. Regular six-month cycle. No concerns.' },
    { patient_id: 'pt_b2c3d4', first_name: 'Arthur', last_name: 'Fung', phone_e164: '+17804559034', email: 'a.fung@shaw.ca', lead_status: 'contacted', tags: ['consult', 'new-patient'], last_contact_at: iso(daysAgo(6)), total_calls: 2, notes: 'Interested in partial denture options. Requested cost breakdown by email.' },
    { patient_id: 'pt_e5f6g7', first_name: 'Evelyn', last_name: 'Flett', phone_e164: '+15879739912', email: 'evelyn.flett@outlook.com', lead_status: 'new', tags: ['emergency', 'new-patient'], last_contact_at: iso(daysAgo(2)), total_calls: 1, notes: 'Chipped front tooth. Called after hours. Booked next available morning slot.' },
    { patient_id: 'pt_h8i9j1', first_name: 'Norman', last_name: 'Fehr', phone_e164: '+17804552876', email: null, lead_status: 'lost', tags: ['consult'], last_contact_at: iso(daysAgo(12)), total_calls: 2, notes: 'Inquired about implant pricing. Did not return follow-up calls. Marked lost after 10-day window.' },
  ];

  // ── NE calls (32) ───────────────────────────────────────────────────
  var s0 = dayAt(0, 9, 12);
  var s1 = dayAt(0, 8, 34);
  var s2 = dayAt(0, 16, 45);
  var s3 = dayAt(0, 10, 5);
  var s4 = dayAt(1, 8, 15);
  var s5 = dayAt(1, 9, 48);
  var s6 = dayAt(1, 17, 22);
  var s7 = dayAt(1, 16, 10);
  var s8 = dayAt(2, 9, 30);
  var s9 = dayAt(2, 8, 5);
  var s10 = dayAt(2, 17, 55);
  var s11 = dayAt(3, 9, 15);
  var s12 = dayAt(3, 16, 30);
  var s13 = dayAt(3, 10, 20);
  var s14 = dayAt(4, 8, 45);
  var s15 = dayAt(4, 17, 10);
  var s16 = dayAt(4, 9, 55);
  var s17 = dayAt(5, 16, 40);
  var s18 = dayAt(5, 9, 20);
  var s19 = dayAt(6, 8, 10);
  var s20 = dayAt(6, 19, 30);
  var s21 = dayAt(7, 9, 5);
  var s22 = dayAt(7, 17, 45);
  var s23 = dayAt(8, 10, 15);
  var s24 = dayAt(8, 8, 50);
  var s25 = dayAt(9, 16, 20);
  var s26 = dayAt(9, 9, 40);
  var s27 = dayAt(10, 19, 15);
  var s28 = dayAt(11, 9, 25);
  var s29 = dayAt(12, 8, 30);
  var s30 = dayAt(13, 17, 5);
  var s31 = dayAt(13, 9, 10);

  var NE_CALLS = [
    { call_id: 'call_a1b2c3d4', started_at: iso(s0), caller_e164: '+15879731042', caller_name: 'Margaret Olsen', patient_id: 'pt_a1b2c3', duration_seconds: 142, outcome: 'booked', transcript_turns: 12, has_patient: true, after_hours: isAfterHoursNE(s0), appointment_id: 'apt_a1b2c3', audio_src: null },
    { call_id: 'call_e5f6g7h8', started_at: iso(s1), caller_e164: '+15879734488', caller_name: 'Donna Fong', patient_id: 'pt_g7h8i9', duration_seconds: 68, outcome: 'booked', transcript_turns: 6, has_patient: true, after_hours: isAfterHoursNE(s1), appointment_id: 'apt_g7h8i9', audio_src: null },
    { call_id: 'call_i9j1k2l3', started_at: iso(s2), caller_e164: '+17804553321', caller_name: 'Robert Makokis', patient_id: 'pt_j1k2l3', duration_seconds: 195, outcome: 'transferred', transcript_turns: 8, has_patient: true, after_hours: isAfterHoursNE(s2), appointment_id: null, audio_src: null },
    { call_id: 'call_m4n5o6p7', started_at: iso(s3), caller_e164: '+15879730412', caller_name: null, patient_id: null, duration_seconds: 52, outcome: 'voicemail', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursNE(s3), appointment_id: null, audio_src: null },
    { call_id: 'call_q8r9s1t2', started_at: iso(s4), caller_e164: '+15879738801', caller_name: 'Patricia Savard', patient_id: 'pt_m4n5o6', duration_seconds: 178, outcome: 'booked', transcript_turns: 14, has_patient: true, after_hours: isAfterHoursNE(s4), appointment_id: 'apt_m4n5o6', audio_src: null },
    { call_id: 'call_u3v4w5x6', started_at: iso(s5), caller_e164: '+15879736643', caller_name: 'Lorraine Flett', patient_id: 'pt_y7z8a1', duration_seconds: 96, outcome: 'booked', transcript_turns: 8, has_patient: true, after_hours: isAfterHoursNE(s5), appointment_id: 'apt_y7z8a1', audio_src: null },
    { call_id: 'call_y7z8a1b2', started_at: iso(s6), caller_e164: '+17804529917', caller_name: 'Gerald Fehr', patient_id: 'pt_d4e5f6', duration_seconds: 134, outcome: 'transferred', transcript_turns: 10, has_patient: true, after_hours: isAfterHoursNE(s6), appointment_id: null, audio_src: null },
    { call_id: 'call_c3d4e5f6', started_at: iso(s7), caller_e164: '+15879730887', caller_name: null, patient_id: null, duration_seconds: 45, outcome: 'missed', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursNE(s7), appointment_id: null, audio_src: null },
    { call_id: 'call_g7h8i9j1', started_at: iso(s8), caller_e164: '+17804557762', caller_name: 'Wayne Chicken', patient_id: 'pt_p7q8r9', duration_seconds: 265, outcome: 'booked', transcript_turns: 22, has_patient: true, after_hours: isAfterHoursNE(s8), appointment_id: 'apt_p7q8r9', audio_src: null },
    { call_id: 'call_k2l3m4n5', started_at: iso(s9), caller_e164: '+15879739912', caller_name: 'Evelyn Flett', patient_id: 'pt_e5f6g7', duration_seconds: 88, outcome: 'booked', transcript_turns: 7, has_patient: true, after_hours: isAfterHoursNE(s9), appointment_id: 'apt_e5f6g7', audio_src: null },
    { call_id: 'call_o6p7q8r9', started_at: iso(s10), caller_e164: '+15879732205', caller_name: 'Helen Brandt', patient_id: 'pt_s1t2u3', duration_seconds: 110, outcome: 'transferred', transcript_turns: 9, has_patient: true, after_hours: isAfterHoursNE(s10), appointment_id: null, audio_src: null },
    { call_id: 'call_s1t2u3v4', started_at: iso(s11), caller_e164: '+17804553321', caller_name: 'Robert Makokis', patient_id: 'pt_j1k2l3', duration_seconds: 155, outcome: 'booked', transcript_turns: 11, has_patient: true, after_hours: isAfterHoursNE(s11), appointment_id: 'apt_j1k2l3', audio_src: null },
    { call_id: 'call_w5x6y7z8', started_at: iso(s12), caller_e164: '+15879730223', caller_name: null, patient_id: null, duration_seconds: 72, outcome: 'voicemail', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursNE(s12), appointment_id: null, audio_src: null },
    { call_id: 'call_a2b3c4d5', started_at: iso(s13), caller_e164: '+17804559034', caller_name: 'Arthur Fung', patient_id: 'pt_b2c3d4', duration_seconds: 130, outcome: 'transferred', transcript_turns: 7, has_patient: true, after_hours: isAfterHoursNE(s13), appointment_id: null, audio_src: null },
    { call_id: 'call_e6f7g8h9', started_at: iso(s14), caller_e164: '+17804551198', caller_name: 'Dennis Favel', patient_id: 'pt_v4w5x6', duration_seconds: 98, outcome: 'booked', transcript_turns: 8, has_patient: true, after_hours: isAfterHoursNE(s14), appointment_id: 'apt_v4w5x6', audio_src: null },
    { call_id: 'call_i1j2k3l4', started_at: iso(s15), caller_e164: '+15879732205', caller_name: 'Helen Brandt', patient_id: 'pt_s1t2u3', duration_seconds: 165, outcome: 'agent_handled', transcript_turns: 14, has_patient: true, after_hours: isAfterHoursNE(s15), appointment_id: null, audio_src: null },
    { call_id: 'call_m5n6o7p8', started_at: iso(s16), caller_e164: '+15879730556', caller_name: null, patient_id: null, duration_seconds: 42, outcome: 'missed', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursNE(s16), appointment_id: null, audio_src: null },
    { call_id: 'call_q9r1s2t3', started_at: iso(s17), caller_e164: '+17804559034', caller_name: 'Arthur Fung', patient_id: 'pt_b2c3d4', duration_seconds: 148, outcome: 'booked', transcript_turns: 10, has_patient: true, after_hours: isAfterHoursNE(s17), appointment_id: 'apt_b2c3d4', audio_src: null },
    { call_id: 'call_u4v5w6x7', started_at: iso(s18), caller_e164: '+17804552876', caller_name: 'Norman Fehr', patient_id: 'pt_h8i9j1', duration_seconds: 85, outcome: 'transferred', transcript_turns: 6, has_patient: true, after_hours: isAfterHoursNE(s18), appointment_id: null, audio_src: null },
    { call_id: 'call_y8z9a1b1', started_at: iso(s19), caller_e164: '+17804529917', caller_name: 'Gerald Fehr', patient_id: 'pt_d4e5f6', duration_seconds: 112, outcome: 'booked', transcript_turns: 9, has_patient: true, after_hours: isAfterHoursNE(s19), appointment_id: 'apt_d4e5f6', audio_src: null },
    { call_id: 'call_c2d3e4f5', started_at: iso(s20), caller_e164: '+15879730991', caller_name: null, patient_id: null, duration_seconds: 78, outcome: 'voicemail', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursNE(s20), appointment_id: null, audio_src: null },
    { call_id: 'call_g6h7i8j9', started_at: iso(s21), caller_e164: '+15879732205', caller_name: 'Helen Brandt', patient_id: 'pt_s1t2u3', duration_seconds: 175, outcome: 'booked', transcript_turns: 13, has_patient: true, after_hours: isAfterHoursNE(s21), appointment_id: 'apt_s1t2u3', audio_src: null },
    { call_id: 'call_k1l2m3n4', started_at: iso(s22), caller_e164: '+15879731042', caller_name: 'Margaret Olsen', patient_id: 'pt_a1b2c3', duration_seconds: 55, outcome: 'transferred', transcript_turns: 5, has_patient: true, after_hours: isAfterHoursNE(s22), appointment_id: null, audio_src: null },
    { call_id: 'call_o5p6q7r8', started_at: iso(s23), caller_e164: '+15879736643', caller_name: 'Lorraine Flett', patient_id: 'pt_y7z8a1', duration_seconds: 92, outcome: 'agent_handled', transcript_turns: 8, has_patient: true, after_hours: isAfterHoursNE(s23), appointment_id: null, audio_src: null },
    { call_id: 'call_s9t1u2v3', started_at: iso(s24), caller_e164: '+15879731042', caller_name: 'Margaret Olsen', patient_id: 'pt_a1b2c3', duration_seconds: 138, outcome: 'booked', transcript_turns: 10, has_patient: true, after_hours: isAfterHoursNE(s24), appointment_id: 'apt_a1b2c4', audio_src: null },
    { call_id: 'call_w4x5y6z7', started_at: iso(s25), caller_e164: '+17804557762', caller_name: 'Wayne Chicken', patient_id: 'pt_p7q8r9', duration_seconds: 162, outcome: 'transferred', transcript_turns: 11, has_patient: true, after_hours: isAfterHoursNE(s25), appointment_id: null, audio_src: null },
    { call_id: 'call_a3b4c5d6', started_at: iso(s26), caller_e164: '+15879739912', caller_name: 'Evelyn Flett', patient_id: 'pt_e5f6g7', duration_seconds: 105, outcome: 'booked', transcript_turns: 9, has_patient: true, after_hours: isAfterHoursNE(s26), appointment_id: 'apt_e5f6g8', audio_src: null },
    { call_id: 'call_e7f8g9h1', started_at: iso(s27), caller_e164: '+15879730334', caller_name: null, patient_id: null, duration_seconds: 68, outcome: 'voicemail', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursNE(s27), appointment_id: null, audio_src: null },
    { call_id: 'call_i2j3k4l5', started_at: iso(s28), caller_e164: '+17804552876', caller_name: 'Norman Fehr', patient_id: 'pt_h8i9j1', duration_seconds: 188, outcome: 'transferred', transcript_turns: 12, has_patient: true, after_hours: isAfterHoursNE(s28), appointment_id: null, audio_src: null },
    { call_id: 'call_m6n7o8p9', started_at: iso(s29), caller_e164: '+15879736643', caller_name: 'Lorraine Flett', patient_id: 'pt_y7z8a1', duration_seconds: 125, outcome: 'booked', transcript_turns: 10, has_patient: true, after_hours: isAfterHoursNE(s29), appointment_id: 'apt_y7z8a2', audio_src: null },
    { call_id: 'call_q1r2s3t4', started_at: iso(s30), caller_e164: '+15879730778', caller_name: null, patient_id: null, duration_seconds: 35, outcome: 'missed', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursNE(s30), appointment_id: null, audio_src: null },
    { call_id: 'call_u5v6w7x8', started_at: iso(s31), caller_e164: '+17804551198', caller_name: 'Dennis Favel', patient_id: 'pt_v4w5x6', duration_seconds: 145, outcome: 'voicemail', transcript_turns: 4, has_patient: true, after_hours: isAfterHoursNE(s31), appointment_id: null, audio_src: null },
  ];

  // ── NE appointments (14 today) ──────────────────────────────────────
  var NE_APPOINTMENTS = [
    { id: 'apt_a1b2c3', patient_id: 'pt_a1b2c3', patient_name: 'Margaret Olsen', provider: 'Dr. Hau Le', time_start: iso(todayAt(9, 30)), time_end: iso(todayAt(10, 30)), procedure: 'Denture fit-and-adjust', booked_by: 'ai', source_call_id: 'call_a1b2c3d4' },
    { id: 'apt_g7h8i9', patient_id: 'pt_g7h8i9', patient_name: 'Donna Fong', provider: 'Dr. Sara Osei', time_start: iso(todayAt(10, 0)), time_end: iso(todayAt(11, 0)), procedure: 'Implant consult', booked_by: 'ai', source_call_id: 'call_e5f6g7h8' },
    { id: 'apt_m4n5o6', patient_id: 'pt_m4n5o6', patient_name: 'Patricia Savard', provider: 'Dr. Hau Le', time_start: iso(todayAt(11, 0)), time_end: iso(todayAt(11, 30)), procedure: 'Emergency denture repair', booked_by: 'ai', source_call_id: 'call_q8r9s1t2' },
    { id: 'apt_y7z8a1', patient_id: 'pt_y7z8a1', patient_name: 'Lorraine Flett', provider: 'Hygienist Maya', time_start: iso(todayAt(9, 0)), time_end: iso(todayAt(10, 0)), procedure: 'Recall + hygiene', booked_by: 'ai', source_call_id: 'call_u3v4w5x6' },
    { id: 'apt_p7q8r9', patient_id: 'pt_p7q8r9', patient_name: 'Wayne Chicken', provider: 'Dr. Sara Osei', time_start: iso(todayAt(13, 0)), time_end: iso(todayAt(14, 0)), procedure: 'Implant consult', booked_by: 'ai', source_call_id: 'call_g7h8i9j1' },
    { id: 'apt_e5f6g7', patient_id: 'pt_e5f6g7', patient_name: 'Evelyn Flett', provider: 'Dr. Hau Le', time_start: iso(todayAt(8, 30)), time_end: iso(todayAt(9, 0)), procedure: 'Emergency assessment', booked_by: 'ai', source_call_id: 'call_k2l3m4n5' },
    { id: 'apt_j1k2l3', patient_id: 'pt_j1k2l3', patient_name: 'Robert Makokis', provider: 'Dr. Hau Le', time_start: iso(todayAt(14, 0)), time_end: iso(todayAt(15, 0)), procedure: 'Denture fit-and-adjust', booked_by: 'ai', source_call_id: 'call_s1t2u3v4' },
    { id: 'apt_v4w5x6', patient_id: 'pt_v4w5x6', patient_name: 'Dennis Favel', provider: 'Dr. Sara Osei', time_start: iso(todayAt(15, 0)), time_end: iso(todayAt(16, 0)), procedure: 'Full assessment', booked_by: 'ai', source_call_id: 'call_e6f7g8h9' },
    { id: 'apt_b2c3d4', patient_id: 'pt_b2c3d4', patient_name: 'Arthur Fung', provider: 'Dr. Hau Le', time_start: iso(todayAt(16, 0)), time_end: iso(todayAt(17, 0)), procedure: 'Partial denture consult', booked_by: 'ai', source_call_id: 'call_q9r1s2t3' },
    { id: 'apt_d4e5f6', patient_id: 'pt_d4e5f6', patient_name: 'Gerald Fehr', provider: 'Hygienist Maya', time_start: iso(todayAt(10, 30)), time_end: iso(todayAt(11, 30)), procedure: 'Recall + hygiene', booked_by: 'ai', source_call_id: 'call_y8z9a1b1' },
    { id: 'apt_s1t2u3', patient_id: 'pt_s1t2u3', patient_name: 'Helen Brandt', provider: 'Dr. Sara Osei', time_start: iso(todayAt(11, 30)), time_end: iso(todayAt(12, 0)), procedure: 'Post-delivery check', booked_by: 'ai', source_call_id: 'call_g6h7i8j9' },
    { id: 'apt_a1b2c4', patient_id: 'pt_a1b2c3', patient_name: 'Margaret Olsen', provider: 'Hygienist Maya', time_start: iso(todayAt(13, 30)), time_end: iso(todayAt(14, 0)), procedure: 'Recall + hygiene', booked_by: 'ai', source_call_id: 'call_s9t1u2v3' },
    { id: 'apt_e5f6g8', patient_id: 'pt_e5f6g7', patient_name: 'Evelyn Flett', provider: 'Dr. Hau Le', time_start: iso(todayAt(12, 0)), time_end: iso(todayAt(12, 30)), procedure: 'Crown delivery', booked_by: 'ai', source_call_id: 'call_a3b4c5d6' },
    { id: 'apt_y7z8a2', patient_id: 'pt_y7z8a1', patient_name: 'Lorraine Flett', provider: 'Dr. Sara Osei', time_start: iso(todayAt(15, 30)), time_end: iso(todayAt(16, 30)), procedure: 'Denture reline', booked_by: 'ai', source_call_id: 'call_m6n7o8p9' },
  ];

  // ── NE transcripts (3 full) ─────────────────────────────────────────

  var neTranscriptShort = {
    turns: [
      { t: 0, speaker: 'agent', text: 'Northeast Denture Clinic, this is the automated assistant. How can I help you today?', confidence: 0.97, intents: [{ name: 'general_information', score: 0.3 }], latency_ms: { stt: 0, llm: 320, tool: 0, tts: 280, total: 600 } },
      { t: 4200, speaker: 'caller', text: 'Hi, I need to book an appointment. My dentist referred me for an implant consult.', confidence: 0.92, intents: [{ name: 'book_appointment', score: 0.91 }, { name: 'general_information', score: 0.06 }, { name: 'ask_provider_availability', score: 0.03 }], latency_ms: { stt: 180, llm: 0, tool: 0, tts: 0, total: 180 } },
      { t: 9800, speaker: 'agent', text: 'Of course. I have an opening this morning at 10:00 with Dr. Sara Osei. Would that work for you?', confidence: 0.95, intents: [{ name: 'book_appointment', score: 0.88 }], latency_ms: { stt: 0, llm: 410, tool: 520, tts: 290, total: 1220 } },
      { t: 15200, speaker: 'caller', text: 'Ten works. My name is Donna Fong.', confidence: 0.94, intents: [{ name: 'book_appointment', score: 0.93 }, { name: 'confirm_address', score: 0.04 }, { name: 'general_information', score: 0.03 }], latency_ms: { stt: 160, llm: 0, tool: 0, tts: 0, total: 160 } },
      { t: 20100, speaker: 'agent', text: 'Confirmed. Donna Fong, implant consult with Dr. Osei at 10:00 today. We will see you then.', confidence: 0.96, intents: [{ name: 'book_appointment', score: 0.95 }], latency_ms: { stt: 0, llm: 380, tool: 610, tts: 310, total: 1300 } },
      { t: 26500, speaker: 'caller', text: 'Thank you.', confidence: 0.98, intents: [{ name: 'general_information', score: 0.9 }, { name: 'book_appointment', score: 0.08 }, { name: 'confirm_address', score: 0.02 }], latency_ms: { stt: 140, llm: 0, tool: 0, tts: 0, total: 140 } },
    ],
    logs: [
      { ts_ms: 0, level: 'info', message: 'Call started', payload: { call_id: 'call_e5f6g7h8', caller: '+15879734488' } },
      { ts_ms: 4200, level: 'info', message: 'Intent classified: book_appointment (0.91)', payload: { top_intent: 'book_appointment' } },
      { ts_ms: 9800, level: 'info', message: 'Schedule lookup: 1 slot available today', payload: { slots: 1 } },
      { ts_ms: 20100, level: 'info', message: 'Appointment created: apt_g7h8i9', payload: { appointment_id: 'apt_g7h8i9' } },
      { ts_ms: 26500, level: 'info', message: 'Call ended normally', payload: { duration_seconds: 68 } },
    ],
    flow_path: ['greet', 'identify_caller', 'check_schedule', 'offer_slots', 'confirm', 'book'],
  };

  var neTranscriptMedium = {
    turns: [
      { t: 0, speaker: 'agent', text: 'Northeast Denture Clinic, automated assistant. How can I help you?', confidence: 0.97, intents: [{ name: 'general_information', score: 0.3 }], latency_ms: { stt: 0, llm: 310, tool: 0, tts: 270, total: 580 } },
      { t: 3800, speaker: 'caller', text: 'Yes, hello. This is Margaret Olsen. I have an upper partial and it has been feeling loose the last few days.', confidence: 0.88, intents: [{ name: 'book_appointment', score: 0.62 }, { name: 'general_information', score: 0.28 }, { name: 'ask_provider_availability', score: 0.10 }], latency_ms: { stt: 210, llm: 0, tool: 0, tts: 0, total: 210 } },
      { t: 10200, speaker: 'agent', text: 'I am sorry to hear that, Margaret. A loose partial can be uncomfortable. Is it causing any pain when you eat or speak?', confidence: 0.94, intents: [{ name: 'book_appointment', score: 0.55 }], latency_ms: { stt: 0, llm: 450, tool: 0, tts: 310, total: 760 } },
      { t: 16800, speaker: 'caller', text: 'Not pain exactly, but it shifts when I chew on the right side. It did not used to do that.', confidence: 0.91, intents: [{ name: 'book_appointment', score: 0.70 }, { name: 'general_information', score: 0.22 }, { name: 'ask_pricing', score: 0.08 }], latency_ms: { stt: 190, llm: 0, tool: 0, tts: 0, total: 190 } },
      { t: 23400, speaker: 'agent', text: 'That sounds like it may need a fit-and-adjust. Dr. Le handles those. Let me check his availability for you.', confidence: 0.95, intents: [{ name: 'book_appointment', score: 0.82 }], latency_ms: { stt: 0, llm: 420, tool: 580, tts: 290, total: 1290 } },
      { t: 30100, speaker: 'caller', text: 'That would be great. Is there anything today?', confidence: 0.93, intents: [{ name: 'ask_provider_availability', score: 0.85 }, { name: 'book_appointment', score: 0.12 }, { name: 'general_information', score: 0.03 }], latency_ms: { stt: 170, llm: 0, tool: 0, tts: 0, total: 170 } },
      { t: 35600, speaker: 'agent', text: 'Dr. Le has an opening at 9:30 this morning. The appointment would be about an hour. Does that work?', confidence: 0.96, intents: [{ name: 'book_appointment', score: 0.90 }], latency_ms: { stt: 0, llm: 390, tool: 480, tts: 300, total: 1170 } },
      { t: 42200, speaker: 'caller', text: 'Nine-thirty is fine. I can be there.', confidence: 0.95, intents: [{ name: 'book_appointment', score: 0.94 }, { name: 'confirm_address', score: 0.04 }, { name: 'general_information', score: 0.02 }], latency_ms: { stt: 150, llm: 0, tool: 0, tts: 0, total: 150 } },
      { t: 47800, speaker: 'agent', text: 'I have you booked. Margaret Olsen, denture fit-and-adjust with Dr. Hau Le at 9:30 today.', confidence: 0.97, intents: [{ name: 'book_appointment', score: 0.96 }], latency_ms: { stt: 0, llm: 360, tool: 640, tts: 280, total: 1280 } },
      { t: 54100, speaker: 'caller', text: 'Do I need to bring anything?', confidence: 0.90, intents: [{ name: 'general_information', score: 0.78 }, { name: 'ask_pricing', score: 0.15 }, { name: 'book_appointment', score: 0.07 }], latency_ms: { stt: 180, llm: 0, tool: 0, tts: 0, total: 180 } },
      { t: 59500, speaker: 'agent', text: 'Just bring the partial itself and your insurance card if you have one on file. We have your records from your last visit.', confidence: 0.94, intents: [{ name: 'general_information', score: 0.85 }], latency_ms: { stt: 0, llm: 440, tool: 0, tts: 320, total: 760 } },
      { t: 65800, speaker: 'caller', text: 'Perfect. Thank you very much.', confidence: 0.97, intents: [{ name: 'general_information', score: 0.92 }, { name: 'book_appointment', score: 0.06 }, { name: 'confirm_address', score: 0.02 }], latency_ms: { stt: 140, llm: 0, tool: 0, tts: 0, total: 140 } },
    ],
    logs: [
      { ts_ms: 0, level: 'info', message: 'Call started', payload: { call_id: 'call_a1b2c3d4', caller: '+15879731042' } },
      { ts_ms: 3800, level: 'info', message: 'Patient matched: pt_a1b2c3 (Margaret Olsen)', payload: { patient_id: 'pt_a1b2c3' } },
      { ts_ms: 10200, level: 'info', message: 'Clarification turn: gathering symptom detail', payload: {} },
      { ts_ms: 23400, level: 'info', message: 'Schedule lookup for Dr. Le', payload: { provider: 'Dr. Hau Le', slots_found: 2 } },
      { ts_ms: 35600, level: 'warn', message: 'Partial confidence on availability intent (0.62 initial)', payload: { initial_score: 0.62 } },
      { ts_ms: 47800, level: 'info', message: 'Appointment created: apt_a1b2c3', payload: { appointment_id: 'apt_a1b2c3' } },
      { ts_ms: 65800, level: 'info', message: 'Call ended normally', payload: { duration_seconds: 142 } },
    ],
    flow_path: ['greet', 'identify_caller', 'clarify_symptoms', 'check_schedule', 'offer_slots', 'confirm', 'book', 'post_booking_info'],
  };

  var neTranscriptLong = {
    turns: [
      { t: 0, speaker: 'agent', text: 'Northeast Denture Clinic, automated assistant. How can I help you?', confidence: 0.97, intents: [{ name: 'general_information', score: 0.3 }], latency_ms: { stt: 0, llm: 300, tool: 0, tts: 260, total: 560 } },
      { t: 3500, speaker: 'caller', text: 'Yeah, I am calling around about implant-supported dentures. What do you charge for a consult?', confidence: 0.90, intents: [{ name: 'ask_pricing', score: 0.88 }, { name: 'book_appointment', score: 0.08 }, { name: 'general_information', score: 0.04 }], latency_ms: { stt: 200, llm: 0, tool: 0, tts: 0, total: 200 } },
      { t: 9200, speaker: 'agent', text: 'The initial consult is complimentary. During that visit, the denturist reviews your case, takes any necessary imaging, and outlines treatment options with costs.', confidence: 0.95, intents: [{ name: 'ask_pricing', score: 0.82 }], latency_ms: { stt: 0, llm: 480, tool: 0, tts: 340, total: 820 } },
      { t: 16100, speaker: 'caller', text: 'Free consult, okay. And what does the actual implant work run? Ballpark.', confidence: 0.87, intents: [{ name: 'ask_pricing', score: 0.92 }, { name: 'general_information', score: 0.05 }, { name: 'book_appointment', score: 0.03 }], latency_ms: { stt: 190, llm: 0, tool: 0, tts: 0, total: 190 } },
      { t: 22800, speaker: 'agent', text: 'Treatment cost depends on the number of implants and the prosthetic design. A two-implant overdenture typically ranges from four to six thousand. The denturist will give you an exact figure at the consult.', confidence: 0.93, intents: [{ name: 'ask_pricing', score: 0.90 }], latency_ms: { stt: 0, llm: 520, tool: 0, tts: 350, total: 870 } },
      { t: 31400, speaker: 'caller', text: 'Does insurance cover any of that?', confidence: 0.91, intents: [{ name: 'ask_pricing', score: 0.75 }, { name: 'general_information', score: 0.20 }, { name: 'book_appointment', score: 0.05 }], latency_ms: { stt: 170, llm: 0, tool: 0, tts: 0, total: 170 } },
      { t: 36900, speaker: 'agent', text: 'Most Alberta Blue Cross and employer plans cover a portion of denture work. The clinic submits a predetermination to your insurer before treatment begins so you know the out-of-pocket amount in advance.', confidence: 0.94, intents: [{ name: 'ask_pricing', score: 0.70 }], latency_ms: { stt: 0, llm: 490, tool: 0, tts: 330, total: 820 } },
      { t: 44200, speaker: 'caller', text: 'Alright. What about timing? How long does the whole process take?', confidence: 0.89, intents: [{ name: 'general_information', score: 0.72 }, { name: 'ask_pricing', score: 0.18 }, { name: 'book_appointment', score: 0.10 }], latency_ms: { stt: 180, llm: 0, tool: 0, tts: 0, total: 180 } },
      { t: 50600, speaker: 'agent', text: 'From consult to final delivery, a two-implant case typically takes three to four months. That includes healing time after implant placement.', confidence: 0.95, intents: [{ name: 'general_information', score: 0.80 }], latency_ms: { stt: 0, llm: 510, tool: 0, tts: 340, total: 850 } },
      { t: 58300, speaker: 'caller', text: 'Three to four months. And who does the surgery part?', confidence: 0.86, intents: [{ name: 'ask_provider_availability', score: 0.65 }, { name: 'general_information', score: 0.30 }, { name: 'book_appointment', score: 0.05 }], latency_ms: { stt: 190, llm: 0, tool: 0, tts: 0, total: 190 } },
      { t: 64100, speaker: 'agent', text: 'The clinic coordinates with an oral surgeon for the implant placement. The denturist handles the prosthetic design, fitting, and all follow-up adjustments.', confidence: 0.94, intents: [{ name: 'general_information', score: 0.82 }], latency_ms: { stt: 0, llm: 460, tool: 0, tts: 310, total: 770 } },
      { t: 71500, speaker: 'caller', text: 'Okay. I have been to two other places already. Your pricing sounds about the same.', confidence: 0.88, intents: [{ name: 'general_information', score: 0.60 }, { name: 'ask_pricing', score: 0.30 }, { name: 'book_appointment', score: 0.10 }], latency_ms: { stt: 200, llm: 0, tool: 0, tts: 0, total: 200 } },
      { t: 77800, speaker: 'agent', text: 'The consult is the best way to compare. The denturist can review any treatment plans you have from other clinics and give you a direct comparison.', confidence: 0.93, intents: [{ name: 'book_appointment', score: 0.55 }], latency_ms: { stt: 0, llm: 470, tool: 0, tts: 320, total: 790 } },
      { t: 85200, speaker: 'caller', text: 'Fair enough. When is the soonest I could come in?', confidence: 0.92, intents: [{ name: 'book_appointment', score: 0.88 }, { name: 'ask_provider_availability', score: 0.10 }, { name: 'general_information', score: 0.02 }], latency_ms: { stt: 170, llm: 0, tool: 0, tts: 0, total: 170 } },
      { t: 91600, speaker: 'agent', text: 'Let me check. Dr. Sara Osei has an opening today at 1:00 PM. Would that work?', confidence: 0.96, intents: [{ name: 'book_appointment', score: 0.90 }], latency_ms: { stt: 0, llm: 400, tool: 620, tts: 290, total: 1310 } },
      { t: 98400, speaker: 'caller', text: 'Today at one? That is fast. Yeah, I can do that.', confidence: 0.94, intents: [{ name: 'book_appointment', score: 0.93 }, { name: 'confirm_address', score: 0.05 }, { name: 'general_information', score: 0.02 }], latency_ms: { stt: 160, llm: 0, tool: 0, tts: 0, total: 160 } },
      { t: 104200, speaker: 'agent', text: 'May I have your name, please?', confidence: 0.97, intents: [{ name: 'book_appointment', score: 0.92 }], latency_ms: { stt: 0, llm: 340, tool: 0, tts: 260, total: 600 } },
      { t: 108800, speaker: 'caller', text: 'Wayne Chicken.', confidence: 0.48, intents: [{ name: 'book_appointment', score: 0.90 }, { name: 'general_information', score: 0.08 }, { name: 'confirm_address', score: 0.02 }], latency_ms: { stt: 150, llm: 0, tool: 0, tts: 0, total: 150 } },
      { t: 113500, speaker: 'agent', text: 'I want to confirm the spelling. Is that C-H-I-C-K-E-N, as in the word?', confidence: 0.92, intents: [{ name: 'book_appointment', score: 0.85 }], latency_ms: { stt: 0, llm: 430, tool: 0, tts: 300, total: 730 } },
      { t: 119200, speaker: 'caller', text: 'Yes, that is correct. Wayne Chicken.', confidence: 0.95, intents: [{ name: 'confirm_address', score: 0.70 }, { name: 'book_appointment', score: 0.25 }, { name: 'general_information', score: 0.05 }], latency_ms: { stt: 160, llm: 0, tool: 0, tts: 0, total: 160 } },
      { t: 125800, speaker: 'agent', text: 'Thank you, Wayne. You are booked for an implant consult with Dr. Sara Osei today at 1:00 PM. Please bring any existing treatment plans from other clinics if you have them.', confidence: 0.96, intents: [{ name: 'book_appointment', score: 0.95 }], latency_ms: { stt: 0, llm: 410, tool: 680, tts: 310, total: 1400 } },
      { t: 135400, speaker: 'caller', text: 'Will do. Thanks.', confidence: 0.97, intents: [{ name: 'general_information', score: 0.90 }, { name: 'book_appointment', score: 0.08 }, { name: 'confirm_address', score: 0.02 }], latency_ms: { stt: 140, llm: 0, tool: 0, tts: 0, total: 140 } },
    ],
    logs: [
      { ts_ms: 0, level: 'info', message: 'Call started', payload: { call_id: 'call_g7h8i9j1', caller: '+17804557762' } },
      { ts_ms: 3500, level: 'info', message: 'Intent classified: ask_pricing (0.88)', payload: { top_intent: 'ask_pricing' } },
      { ts_ms: 9200, level: 'info', message: 'Pricing FAQ served: complimentary consult', payload: {} },
      { ts_ms: 22800, level: 'info', message: 'Pricing FAQ served: implant range', payload: {} },
      { ts_ms: 36900, level: 'info', message: 'Insurance FAQ served: predetermination', payload: {} },
      { ts_ms: 77800, level: 'info', message: 'Nudge toward booking after comparison-shopping signals', payload: {} },
      { ts_ms: 91600, level: 'info', message: 'Schedule lookup for Dr. Osei', payload: { provider: 'Dr. Sara Osei', slots_found: 1 } },
      { ts_ms: 108800, level: 'warn', message: 'Low STT confidence on caller name (0.48)', payload: { raw: 'Wayne Chicken', confidence: 0.48 } },
      { ts_ms: 113500, level: 'info', message: 'Name confirmation turn triggered', payload: {} },
      { ts_ms: 125800, level: 'info', message: 'Appointment created: apt_p7q8r9', payload: { appointment_id: 'apt_p7q8r9' } },
      { ts_ms: 135400, level: 'info', message: 'Call ended normally', payload: { duration_seconds: 265 } },
    ],
    flow_path: ['greet', 'identify_intent', 'pricing_faq', 'insurance_faq', 'timeline_faq', 'provider_info', 'nudge_booking', 'check_schedule', 'offer_slots', 'collect_name', 'confirm_name', 'confirm', 'book'],
  };

  var NE_TRANSCRIPTS = {};
  NE_TRANSCRIPTS['call_e5f6g7h8'] = neTranscriptShort;
  NE_TRANSCRIPTS['call_a1b2c3d4'] = neTranscriptMedium;
  NE_TRANSCRIPTS['call_g7h8i9j1'] = neTranscriptLong;

  // ══════════════════════════════════════════════════════════════════════
  // MARKET MALL DENTURE CLINIC — 7 patients, 18 calls, 9 appointments
  // ══════════════════════════════════════════════════════════════════════

  var MM_PATIENTS = [
    { patient_id: 'pt_mm01', first_name: 'Linh', last_name: 'Nguyen', phone_e164: '+14034519823', email: 'linh.nguyen@gmail.com', lead_status: 'booked', tags: ['denture-fitting', 'recall'], last_contact_at: iso(daysAgo(0)), total_calls: 3, notes: 'Upper partial adjustment. Regular recall patient. Insurance through Sun Life.' },
    { patient_id: 'pt_mm02', first_name: 'James', last_name: 'Whitford', phone_e164: '+14034527741', email: null, lead_status: 'new', tags: ['new-patient', 'consult'], last_contact_at: iso(daysAgo(1)), total_calls: 1, notes: 'First-time caller. Interested in full lower denture. Referred by family member.' },
    { patient_id: 'pt_mm03', first_name: 'Priya', last_name: 'Sharma', phone_e164: '+14034538856', email: 'priya.sharma@outlook.com', lead_status: 'booked', tags: ['emergency'], last_contact_at: iso(daysAgo(2)), total_calls: 2, notes: 'Cracked upper denture. Emergency repair completed. Follow-up scheduled.' },
    { patient_id: 'pt_mm04', first_name: 'Douglas', last_name: 'Bearpaw', phone_e164: '+14034541190', email: 'd.bearpaw@shaw.ca', lead_status: 'contacted', tags: ['consult'], last_contact_at: iso(daysAgo(4)), total_calls: 2, notes: 'Inquired about implant-supported options. Waiting on insurance predetermination.' },
    { patient_id: 'pt_mm05', first_name: 'Sandra', last_name: 'Makokis', phone_e164: '+14034556632', email: 'sandra.m@telus.net', lead_status: 'completed', tags: ['denture-fitting', 'recall'], last_contact_at: iso(daysAgo(6)), total_calls: 4, notes: 'Lower complete denture delivered. Final check done. Next recall in 6 months.' },
    { patient_id: 'pt_mm06', first_name: 'Kevin', last_name: 'Tran', phone_e164: '+14034567718', email: null, lead_status: 'new', tags: ['new-patient'], last_contact_at: iso(daysAgo(3)), total_calls: 1, notes: 'Walk-in referral from mall kiosk. Needs initial assessment.' },
    { patient_id: 'pt_mm07', first_name: 'Fatima', last_name: 'Al-Rashid', phone_e164: '+14034578804', email: 'fatima.ar@gmail.com', lead_status: 'lost', tags: ['consult'], last_contact_at: iso(daysAgo(10)), total_calls: 2, notes: 'Called twice about partial denture pricing. Did not book. Marked lost after follow-up window.' },
  ];

  // ── MM calls (18): 10 booked, 4 transferred, 2 voicemail, 2 missed ──
  var mm0 = dayAt(0, 9, 22);
  var mm1 = dayAt(0, 10, 45);
  var mm2 = dayAt(0, 14, 10);
  var mm3 = dayAt(1, 9, 5);
  var mm4 = dayAt(1, 11, 30);
  var mm5 = dayAt(1, 16, 50);
  var mm6 = dayAt(2, 9, 40);
  var mm7 = dayAt(2, 15, 15);
  var mm8 = dayAt(3, 10, 10);
  var mm9 = dayAt(3, 14, 35);
  var mm10 = dayAt(4, 9, 15);
  var mm11 = dayAt(5, 11, 20);
  var mm12 = dayAt(6, 9, 50);
  var mm13 = dayAt(7, 10, 30);
  var mm14 = dayAt(8, 14, 5);
  var mm15 = dayAt(9, 9, 35);
  var mm16 = dayAt(11, 10, 15);
  var mm17 = dayAt(13, 9, 45);

  var MM_CALLS = [
    { call_id: 'call_mm01', started_at: iso(mm0), caller_e164: '+14034519823', caller_name: 'Linh Nguyen', patient_id: 'pt_mm01', duration_seconds: 118, outcome: 'booked', transcript_turns: 10, has_patient: true, after_hours: isAfterHoursMM(mm0), appointment_id: 'apt_mm01', audio_src: null },
    { call_id: 'call_mm02', started_at: iso(mm1), caller_e164: '+14034527741', caller_name: 'James Whitford', patient_id: 'pt_mm02', duration_seconds: 85, outcome: 'booked', transcript_turns: 7, has_patient: true, after_hours: isAfterHoursMM(mm1), appointment_id: 'apt_mm02', audio_src: null },
    { call_id: 'call_mm03', started_at: iso(mm2), caller_e164: '+14034538856', caller_name: 'Priya Sharma', patient_id: 'pt_mm03', duration_seconds: 152, outcome: 'transferred', transcript_turns: 9, has_patient: true, after_hours: isAfterHoursMM(mm2), appointment_id: null, audio_src: null },
    { call_id: 'call_mm04', started_at: iso(mm3), caller_e164: '+14034519823', caller_name: 'Linh Nguyen', patient_id: 'pt_mm01', duration_seconds: 95, outcome: 'booked', transcript_turns: 8, has_patient: true, after_hours: isAfterHoursMM(mm3), appointment_id: 'apt_mm03', audio_src: null },
    { call_id: 'call_mm05', started_at: iso(mm4), caller_e164: '+14034541190', caller_name: 'Douglas Bearpaw', patient_id: 'pt_mm04', duration_seconds: 210, outcome: 'transferred', transcript_turns: 14, has_patient: true, after_hours: isAfterHoursMM(mm4), appointment_id: null, audio_src: null },
    { call_id: 'call_mm06', started_at: iso(mm5), caller_e164: '+14034530112', caller_name: null, patient_id: null, duration_seconds: 62, outcome: 'voicemail', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursMM(mm5), appointment_id: null, audio_src: null },
    { call_id: 'call_mm07', started_at: iso(mm6), caller_e164: '+14034538856', caller_name: 'Priya Sharma', patient_id: 'pt_mm03', duration_seconds: 130, outcome: 'booked', transcript_turns: 11, has_patient: true, after_hours: isAfterHoursMM(mm6), appointment_id: 'apt_mm04', audio_src: null },
    { call_id: 'call_mm08', started_at: iso(mm7), caller_e164: '+14034556632', caller_name: 'Sandra Makokis', patient_id: 'pt_mm05', duration_seconds: 78, outcome: 'booked', transcript_turns: 6, has_patient: true, after_hours: isAfterHoursMM(mm7), appointment_id: 'apt_mm05', audio_src: null },
    { call_id: 'call_mm09', started_at: iso(mm8), caller_e164: '+14034567718', caller_name: 'Kevin Tran', patient_id: 'pt_mm06', duration_seconds: 105, outcome: 'booked', transcript_turns: 8, has_patient: true, after_hours: isAfterHoursMM(mm8), appointment_id: 'apt_mm06', audio_src: null },
    { call_id: 'call_mm10', started_at: iso(mm9), caller_e164: '+14034578804', caller_name: 'Fatima Al-Rashid', patient_id: 'pt_mm07', duration_seconds: 175, outcome: 'transferred', transcript_turns: 12, has_patient: true, after_hours: isAfterHoursMM(mm9), appointment_id: null, audio_src: null },
    { call_id: 'call_mm11', started_at: iso(mm10), caller_e164: '+14034541190', caller_name: 'Douglas Bearpaw', patient_id: 'pt_mm04', duration_seconds: 140, outcome: 'booked', transcript_turns: 10, has_patient: true, after_hours: isAfterHoursMM(mm10), appointment_id: 'apt_mm07', audio_src: null },
    { call_id: 'call_mm12', started_at: iso(mm11), caller_e164: '+14034556632', caller_name: 'Sandra Makokis', patient_id: 'pt_mm05', duration_seconds: 92, outcome: 'booked', transcript_turns: 7, has_patient: true, after_hours: isAfterHoursMM(mm11), appointment_id: 'apt_mm08', audio_src: null },
    { call_id: 'call_mm13', started_at: iso(mm12), caller_e164: '+14034530445', caller_name: null, patient_id: null, duration_seconds: 38, outcome: 'missed', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursMM(mm12), appointment_id: null, audio_src: null },
    { call_id: 'call_mm14', started_at: iso(mm13), caller_e164: '+14034578804', caller_name: 'Fatima Al-Rashid', patient_id: 'pt_mm07', duration_seconds: 160, outcome: 'transferred', transcript_turns: 11, has_patient: true, after_hours: isAfterHoursMM(mm13), appointment_id: null, audio_src: null },
    { call_id: 'call_mm15', started_at: iso(mm14), caller_e164: '+14034519823', caller_name: 'Linh Nguyen', patient_id: 'pt_mm01', duration_seconds: 72, outcome: 'booked', transcript_turns: 6, has_patient: true, after_hours: isAfterHoursMM(mm14), appointment_id: 'apt_mm09', audio_src: null },
    { call_id: 'call_mm16', started_at: iso(mm15), caller_e164: '+14034530778', caller_name: null, patient_id: null, duration_seconds: 55, outcome: 'voicemail', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursMM(mm15), appointment_id: null, audio_src: null },
    { call_id: 'call_mm17', started_at: iso(mm16), caller_e164: '+14034527741', caller_name: 'James Whitford', patient_id: 'pt_mm02', duration_seconds: 98, outcome: 'booked', transcript_turns: 8, has_patient: true, after_hours: isAfterHoursMM(mm16), appointment_id: null, audio_src: null },
    { call_id: 'call_mm18', started_at: iso(mm17), caller_e164: '+14034530221', caller_name: null, patient_id: null, duration_seconds: 30, outcome: 'missed', transcript_turns: 0, has_patient: false, after_hours: isAfterHoursMM(mm17), appointment_id: null, audio_src: null },
  ];

  // ── MM appointments (9 today): 6 AI-booked, 3 front-desk ───────────
  var MM_APPOINTMENTS = [
    { id: 'apt_mm01', patient_id: 'pt_mm01', patient_name: 'Linh Nguyen', provider: 'Dr. Tran', time_start: iso(todayAt(9, 0)), time_end: iso(todayAt(10, 0)), procedure: 'Partial denture adjustment', booked_by: 'ai', source_call_id: 'call_mm01' },
    { id: 'apt_mm02', patient_id: 'pt_mm02', patient_name: 'James Whitford', provider: 'Dr. Singh', time_start: iso(todayAt(10, 0)), time_end: iso(todayAt(11, 0)), procedure: 'Full lower denture consult', booked_by: 'ai', source_call_id: 'call_mm02' },
    { id: 'apt_mm03', patient_id: 'pt_mm01', patient_name: 'Linh Nguyen', provider: 'Hygienist Maya', time_start: iso(todayAt(11, 0)), time_end: iso(todayAt(11, 30)), procedure: 'Recall + hygiene', booked_by: 'ai', source_call_id: 'call_mm04' },
    { id: 'apt_mm04', patient_id: 'pt_mm03', patient_name: 'Priya Sharma', provider: 'Dr. Tran', time_start: iso(todayAt(11, 30)), time_end: iso(todayAt(12, 0)), procedure: 'Emergency denture repair follow-up', booked_by: 'ai', source_call_id: 'call_mm07' },
    { id: 'apt_mm05', patient_id: 'pt_mm05', patient_name: 'Sandra Makokis', provider: 'Dr. Singh', time_start: iso(todayAt(13, 0)), time_end: iso(todayAt(13, 30)), procedure: 'Post-delivery check', booked_by: 'ai', source_call_id: 'call_mm08' },
    { id: 'apt_mm06', patient_id: 'pt_mm06', patient_name: 'Kevin Tran', provider: 'Dr. Tran', time_start: iso(todayAt(14, 0)), time_end: iso(todayAt(15, 0)), procedure: 'Initial assessment', booked_by: 'ai', source_call_id: 'call_mm09' },
    { id: 'apt_mm07', patient_id: 'pt_mm04', patient_name: 'Douglas Bearpaw', provider: 'Dr. Singh', time_start: iso(todayAt(15, 0)), time_end: iso(todayAt(16, 0)), procedure: 'Implant consult', booked_by: 'front-desk', source_call_id: null },
    { id: 'apt_mm08', patient_id: 'pt_mm05', patient_name: 'Sandra Makokis', provider: 'Hygienist Maya', time_start: iso(todayAt(13, 30)), time_end: iso(todayAt(14, 0)), procedure: 'Recall + hygiene', booked_by: 'front-desk', source_call_id: null },
    { id: 'apt_mm09', patient_id: 'pt_mm01', patient_name: 'Linh Nguyen', provider: 'Dr. Tran', time_start: iso(todayAt(16, 0)), time_end: iso(todayAt(16, 30)), procedure: 'Denture reline', booked_by: 'front-desk', source_call_id: null },
  ];

  // ── MM transcripts (2) ──────────────────────────────────────────────

  var mmTranscriptShort = {
    turns: [
      { t: 0, speaker: 'agent', text: 'Market Mall Denture Clinic, automated assistant. How can I help you today?', confidence: 0.96, intents: [{ name: 'general_information', score: 0.3 }], latency_ms: { stt: 0, llm: 310, tool: 0, tts: 270, total: 580 } },
      { t: 3900, speaker: 'caller', text: 'Hi, I would like to book an appointment for a denture adjustment.', confidence: 0.93, intents: [{ name: 'book_appointment', score: 0.90 }, { name: 'general_information', score: 0.07 }, { name: 'ask_provider_availability', score: 0.03 }], latency_ms: { stt: 175, llm: 0, tool: 0, tts: 0, total: 175 } },
      { t: 8500, speaker: 'agent', text: 'Of course. Dr. Tran has an opening at 9:00 this morning. Would that work?', confidence: 0.95, intents: [{ name: 'book_appointment', score: 0.88 }], latency_ms: { stt: 0, llm: 400, tool: 510, tts: 285, total: 1195 } },
      { t: 14200, speaker: 'caller', text: 'Nine works. My name is Linh Nguyen.', confidence: 0.94, intents: [{ name: 'book_appointment', score: 0.92 }, { name: 'confirm_address', score: 0.05 }, { name: 'general_information', score: 0.03 }], latency_ms: { stt: 165, llm: 0, tool: 0, tts: 0, total: 165 } },
      { t: 19800, speaker: 'agent', text: 'Confirmed. Linh Nguyen, partial denture adjustment with Dr. Tran at 9:00 today.', confidence: 0.96, intents: [{ name: 'book_appointment', score: 0.95 }], latency_ms: { stt: 0, llm: 370, tool: 600, tts: 295, total: 1265 } },
      { t: 25100, speaker: 'caller', text: 'Thank you.', confidence: 0.98, intents: [{ name: 'general_information', score: 0.91 }, { name: 'book_appointment', score: 0.07 }, { name: 'confirm_address', score: 0.02 }], latency_ms: { stt: 140, llm: 0, tool: 0, tts: 0, total: 140 } },
    ],
    logs: [
      { ts_ms: 0, level: 'info', message: 'Call started', payload: { call_id: 'call_mm01', caller: '+14034519823' } },
      { ts_ms: 3900, level: 'info', message: 'Intent classified: book_appointment (0.90)', payload: { top_intent: 'book_appointment' } },
      { ts_ms: 8500, level: 'info', message: 'Schedule lookup: 1 slot available today', payload: { slots: 1 } },
      { ts_ms: 19800, level: 'info', message: 'Appointment created: apt_mm01', payload: { appointment_id: 'apt_mm01' } },
      { ts_ms: 25100, level: 'info', message: 'Call ended normally', payload: { duration_seconds: 118 } },
    ],
    flow_path: ['greet', 'identify_caller', 'check_schedule', 'offer_slots', 'confirm', 'book'],
  };

  var mmTranscriptMedium = {
    turns: [
      { t: 0, speaker: 'agent', text: 'Market Mall Denture Clinic, automated assistant. How can I help you?', confidence: 0.97, intents: [{ name: 'general_information', score: 0.3 }], latency_ms: { stt: 0, llm: 305, tool: 0, tts: 265, total: 570 } },
      { t: 3600, speaker: 'caller', text: 'Hello, this is Priya Sharma. I had my denture repaired last week and it cracked again in the same spot.', confidence: 0.89, intents: [{ name: 'book_appointment', score: 0.65 }, { name: 'general_information', score: 0.25 }, { name: 'ask_provider_availability', score: 0.10 }], latency_ms: { stt: 205, llm: 0, tool: 0, tts: 0, total: 205 } },
      { t: 9800, speaker: 'agent', text: 'I am sorry to hear that, Priya. A repeat fracture in the same area may need a different repair approach. Let me check when Dr. Tran can see you.', confidence: 0.94, intents: [{ name: 'book_appointment', score: 0.72 }], latency_ms: { stt: 0, llm: 440, tool: 560, tts: 305, total: 1305 } },
      { t: 16400, speaker: 'caller', text: 'Is there anything today? I cannot eat properly with it like this.', confidence: 0.92, intents: [{ name: 'ask_provider_availability', score: 0.82 }, { name: 'book_appointment', score: 0.15 }, { name: 'general_information', score: 0.03 }], latency_ms: { stt: 185, llm: 0, tool: 0, tts: 0, total: 185 } },
      { t: 22100, speaker: 'agent', text: 'Dr. Tran has an opening at 11:30 this morning. It would be a 30-minute slot for the assessment and repair.', confidence: 0.95, intents: [{ name: 'book_appointment', score: 0.88 }], latency_ms: { stt: 0, llm: 395, tool: 490, tts: 295, total: 1180 } },
      { t: 28500, speaker: 'caller', text: 'Eleven-thirty is fine. I will be there.', confidence: 0.94, intents: [{ name: 'book_appointment', score: 0.93 }, { name: 'confirm_address', score: 0.04 }, { name: 'general_information', score: 0.03 }], latency_ms: { stt: 155, llm: 0, tool: 0, tts: 0, total: 155 } },
      { t: 33800, speaker: 'agent', text: 'Booked. Priya Sharma, emergency denture repair follow-up with Dr. Tran at 11:30 today. Please bring the denture with you.', confidence: 0.96, intents: [{ name: 'book_appointment', score: 0.95 }], latency_ms: { stt: 0, llm: 365, tool: 620, tts: 285, total: 1270 } },
      { t: 40200, speaker: 'caller', text: 'Will do. Thank you.', confidence: 0.97, intents: [{ name: 'general_information', score: 0.90 }, { name: 'book_appointment', score: 0.08 }, { name: 'confirm_address', score: 0.02 }], latency_ms: { stt: 145, llm: 0, tool: 0, tts: 0, total: 145 } },
    ],
    logs: [
      { ts_ms: 0, level: 'info', message: 'Call started', payload: { call_id: 'call_mm07', caller: '+14034538856' } },
      { ts_ms: 3600, level: 'info', message: 'Patient matched: pt_mm03 (Priya Sharma)', payload: { patient_id: 'pt_mm03' } },
      { ts_ms: 9800, level: 'info', message: 'Repeat issue detected: same fracture location', payload: {} },
      { ts_ms: 22100, level: 'info', message: 'Schedule lookup for Dr. Tran', payload: { provider: 'Dr. Tran', slots_found: 2 } },
      { ts_ms: 33800, level: 'info', message: 'Appointment created: apt_mm04', payload: { appointment_id: 'apt_mm04' } },
      { ts_ms: 40200, level: 'info', message: 'Call ended normally', payload: { duration_seconds: 130 } },
    ],
    flow_path: ['greet', 'identify_caller', 'clarify_issue', 'check_schedule', 'offer_slots', 'confirm', 'book'],
  };

  var MM_TRANSCRIPTS = {};
  MM_TRANSCRIPTS['call_mm01'] = mmTranscriptShort;
  MM_TRANSCRIPTS['call_mm07'] = mmTranscriptMedium;

  // ══════════════════════════════════════════════════════════════════════
  // Assemble CLINICS and expose API
  // ══════════════════════════════════════════════════════════════════════

  var NE_OPTS = { name: 'Northeast Denture Clinic', tz: 'America/Edmonton', acv: 65000,
                  calls: NE_CALLS, transcripts: NE_TRANSCRIPTS,
                  patients: NE_PATIENTS, appointments: NE_APPOINTMENTS };

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

  // Resolve the current clinic id LAZILY on every call. lib/auth.js may not
  // be loaded yet when this script first runs, so we can't pin it at load
  // time. Falls back to STATE (last-seen) and then to the first clinic.
  function resolveCurrentClinicId() {
    var fromAuth = (window.RRD && window.RRD.getCurrentClinicId && window.RRD.getCurrentClinicId());
    if (fromAuth && CLINICS[fromAuth]) {
      STATE.CURRENT_CLINIC_ID = fromAuth;
      return fromAuth;
    }
    if (CLINICS[STATE.CURRENT_CLINIC_ID]) return STATE.CURRENT_CLINIC_ID;
    return Object.keys(CLINICS)[0];
  }

  function getClinic() {
    var id = resolveCurrentClinicId();
    var c = CLINICS[id];
    if (!c) return null;
    var ai = (window.AI_CONFIG && window.AI_CONFIG[id]) || {};
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

  // Don't use Object.assign for the property getters — Object.assign reads
  // the getter once and copies the resolved value, killing the getter.
  // Use defineProperties so the getters survive and re-evaluate on every read.
  STATE.CLINICS = CLINICS;
  STATE.getClinic = getClinic;
  STATE.setCurrentClinic = setCurrentClinic;
  Object.defineProperties(STATE, {
    CLINIC:       { get: function () { return (getClinic() || {}).CLINIC; },       enumerable: true, configurable: true },
    KPIS:         { get: function () { return (getClinic() || {}).KPIS; },         enumerable: true, configurable: true },
    CALLS:        { get: function () { return (getClinic() || {}).CALLS; },        enumerable: true, configurable: true },
    TRANSCRIPTS:  { get: function () { return (getClinic() || {}).TRANSCRIPTS; },  enumerable: true, configurable: true },
    PATIENTS:     { get: function () { return (getClinic() || {}).PATIENTS; },     enumerable: true, configurable: true },
    APPOINTMENTS: { get: function () { return (getClinic() || {}).APPOINTMENTS; }, enumerable: true, configurable: true },
    ROUTING:      { get: function () { return (getClinic() || {}).ROUTING; },      enumerable: true, configurable: true },
    GREETING:     { get: function () { return (getClinic() || {}).GREETING; },     enumerable: true, configurable: true },
  });
  return STATE;
})();
