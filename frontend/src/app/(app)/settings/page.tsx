'use client';

import React from 'react';
import { useToast } from '@/components/overlays/ToastContext';
import { api, ApiError } from '@/lib/api';

// When NEXT_PUBLIC_USE_MOCKS=1, the page renders entirely from the seeds below
// (useful when the FastAPI backend is offline). Otherwise it loads from the API
// on mount, falls back to the seeds if the load fails, and persists every save.
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === '1';

const TABS = ['Clinic info','Working hours','Operatories','Providers','Users & roles','Integrations','Notifications','Audit log','Voice & Persona','AI Disclosure','Services','Knowledge'];
const DAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

// Mirrors the AI_CONFIG structure used by the design-system prototypes (admin-voice.html etc.).
const PROVIDER_TITLES = ['Doctor', 'Denturist', 'Hygienist', 'Dentist'];
const LANGUAGES = [
  { value: 'en-US', label: 'English (US)' },
  { value: 'en-CA', label: 'English (CA)' },
  { value: 'es-US', label: 'Spanish (US)' },
  { value: 'fr-CA', label: 'French (CA)' },
];

interface VoiceCfg { assistant_name: string; provider_title: string; reason_question: string; language: string }
interface DisclosureCfg { ai_disclosure_required: boolean; ai_disclosure_phrase: string; last_reviewed_at: string }
interface AiService { id: string; name: string; duration_min: number; base_price: number; bookable: boolean }
interface KnowledgeDoc { filename: string; title: string; last_updated: string; word_count: number; body: string }

const VOICE_DEFAULTS: VoiceCfg = {
  assistant_name: 'Dental AI',
  provider_title: 'Denturist',
  reason_question: 'What brings you in?',
  language: 'en-US',
};

const DISCLOSURE_DEFAULTS: DisclosureCfg = {
  ai_disclosure_required: true,
  ai_disclosure_phrase: 'Hi, this is the AI receptionist for Oak Dental Calgary. I am not a human — I can book, reschedule, or transfer you to the front desk.',
  last_reviewed_at: '2026-04-12T00:00:00Z',
};

const SERVICES_SEED: AiService[] = [
  { id: 'SVC-001', name: 'Recall exam', duration_min: 30, base_price: 145.00, bookable: true },
  { id: 'SVC-002', name: 'Hygiene · scaling', duration_min: 30, base_price: 95.00, bookable: true },
  { id: 'SVC-003', name: 'New patient consult', duration_min: 30, base_price: 0, bookable: true },
  { id: 'SVC-004', name: 'Crown prep · #36', duration_min: 60, base_price: 580.00, bookable: false },
  { id: 'SVC-005', name: 'Denture reline', duration_min: 45, base_price: 285.00, bookable: false },
  { id: 'SVC-006', name: 'Implant follow-up', duration_min: 30, base_price: 0, bookable: false },
];

const KNOWLEDGE_SEED: KnowledgeDoc[] = [
  {
    filename: 'practice_info.md',
    title: 'Practice info — hours, address, parking',
    last_updated: '2026-04-22',
    word_count: 184,
    body: '# Practice info\n\n## Hours\nMonday–Friday 8:00 AM – 5:00 PM\nSaturday 9:00 AM – 2:00 PM\nSunday closed\n\n## Address\n1420 17 Ave SW, Calgary, AB T2T 0B9\n\n## Parking\nFree two-hour parking on 17 Ave. Underground parkade entrance off 14 St SW.\n\n## Phone\n403-555-0180 (front desk) · 403-555-0911 (after-hours emergency line)',
  },
  {
    filename: 'denture_faq.md',
    title: 'Denture FAQ — most common caller questions',
    last_updated: '2026-04-15',
    word_count: 412,
    body: '# Denture FAQ\n\n## Do I need a referral?\nNo — denturists can be seen without a dentist referral in Alberta.\n\n## How long does a complete denture take?\nFour to six visits over three to four weeks. Initial impression, custom tray, wax try-in, fit, and one or two adjustment visits.\n\n## Does insurance cover dentures?\nMost plans cover 50–60% of complete dentures every 5 years. Bring your card and we will run a pre-determination.\n\n## Can I eat normally with new dentures?\nStart with soft foods for the first week. Cut food into small pieces and chew on both sides at the same time. Avoid sticky foods like caramel for the first month.',
  },
  {
    filename: 'insurance_carriers.md',
    title: 'Accepted insurance carriers',
    last_updated: '2026-03-30',
    word_count: 96,
    body: '# Accepted insurance\n\n- Alberta Blue Cross\n- Sun Life\n- Manulife\n- Canada Life\n- Pacific Blue Cross\n- Alberta Health (AB Adult Dental Plan)\n\nWe direct-bill all of the above. For carriers not listed, we provide a receipt for self-submission.',
  },
];

export default function SettingsPage() {
  const { addToast } = useToast();
  const [tab, setTab] = React.useState(0);

  // Voice & Persona — dirty tracking; API-loaded on mount.
  const [voiceDraft, setVoiceDraft] = React.useState<VoiceCfg>(VOICE_DEFAULTS);
  const [voiceSaved, setVoiceSaved] = React.useState<VoiceCfg>(VOICE_DEFAULTS);
  const [isVoiceLoaded, setIsVoiceLoaded] = React.useState(USE_MOCKS);
  const voiceDirty = JSON.stringify(voiceDraft) !== JSON.stringify(voiceSaved);

  // AI Disclosure — dirty tracking; API-loaded on mount.
  const [discDraft, setDiscDraft] = React.useState<DisclosureCfg>(DISCLOSURE_DEFAULTS);
  const [discSaved, setDiscSaved] = React.useState<DisclosureCfg>(DISCLOSURE_DEFAULTS);
  const [isDisclosureLoaded, setIsDisclosureLoaded] = React.useState(USE_MOCKS);
  const discDirty = JSON.stringify(discDraft) !== JSON.stringify(discSaved);
  const discCharLen = discDraft.ai_disclosure_phrase.length;
  const discCharClass = discCharLen > 280 ? 'char-over' : discCharLen > 240 ? 'char-warn' : 'char-normal';
  const discReviewedDate = (() => {
    try {
      return new Date(discSaved.last_reviewed_at).toISOString().slice(0, 10);
    } catch {
      return 'N/A';
    }
  })();

  // Services — bookable toggle state. id is string-formatted for the UI but
  // we track the integer service_id from the backend so toggle calls hit
  // /api/v2/settings/ai/services-bookable/{id}.
  const [services, setServices] = React.useState<AiService[]>(SERVICES_SEED);
  const [serviceIdMap, setServiceIdMap] = React.useState<Record<string, number>>({});
  const [isServicesLoaded, setIsServicesLoaded] = React.useState(USE_MOCKS);
  const fmtPrice = (p: number) => p === 0 ? '—' : '$' + p.toFixed(2);

  // Knowledge — expanded rows + body edits.
  const [knowledge, setKnowledge] = React.useState<KnowledgeDoc[]>(KNOWLEDGE_SEED);
  const [openDocs, setOpenDocs] = React.useState<Record<string, boolean>>({});
  const [isKnowledgeLoaded, setIsKnowledgeLoaded] = React.useState(USE_MOCKS);
  const toggleDoc = (filename: string) => setOpenDocs(prev => ({ ...prev, [filename]: !prev[filename] }));

  // ── Initial load from API ────────────────────────────────────────────
  React.useEffect(() => {
    if (USE_MOCKS) return;
    let cancelled = false;
    (async () => {
      try {
        const [v, d, sv, kn] = await Promise.all([
          api.v2.settings.ai.voice.get(),
          api.v2.settings.ai.disclosure.get(),
          api.v2.settings.ai.servicesBookable.list(),
          api.v2.settings.ai.knowledge.list(),
        ]);
        if (cancelled) return;
        const vCfg: VoiceCfg = {
          assistant_name: v.assistant_name,
          provider_title: v.provider_title,
          reason_question: v.reason_question,
          language: v.language,
        };
        setVoiceDraft(vCfg);
        setVoiceSaved(vCfg);
        setIsVoiceLoaded(true);
        const dCfg: DisclosureCfg = {
          ai_disclosure_required: d.required,
          ai_disclosure_phrase: d.phrase,
          last_reviewed_at: d.last_reviewed_at ?? new Date().toISOString(),
        };
        setDiscDraft(dCfg);
        setDiscSaved(dCfg);
        setIsDisclosureLoaded(true);
        if (sv.length > 0) {
          const mapped: AiService[] = sv.map(s => ({
            id: `SVC-${String(s.service_id).padStart(3, '0')}`,
            name: s.name,
            duration_min: s.duration_min ?? 30,
            base_price: s.base_price ?? 0,
            bookable: s.bookable,
          }));
          const idMap: Record<string, number> = {};
          sv.forEach(s => { idMap[`SVC-${String(s.service_id).padStart(3, '0')}`] = s.service_id; });
          setServices(mapped);
          setServiceIdMap(idMap);
        }
        setIsServicesLoaded(true);
        if (kn.length > 0) {
          // Hydrate body lazily; list endpoint returns metadata only.
          const docs: KnowledgeDoc[] = await Promise.all(
            kn.map(async k => {
              try {
                const full = await api.v2.settings.ai.knowledge.get(k.filename);
                return {
                  filename: full.filename,
                  title: full.title,
                  last_updated: (full.updated_at ?? '').slice(0, 10),
                  word_count: full.word_count,
                  body: full.body,
                };
              } catch {
                return {
                  filename: k.filename,
                  title: k.title,
                  last_updated: (k.updated_at ?? '').slice(0, 10),
                  word_count: k.word_count,
                  body: '',
                };
              }
            }),
          );
          if (!cancelled) setKnowledge(docs);
        }
        setIsKnowledgeLoaded(true);
      } catch (e) {
        // Backend unavailable — keep seed defaults so the page still renders.
        if (!(e instanceof ApiError)) console.warn('Settings AI load failed:', e);
        // Mark as loaded even on error so UI doesn't hang
        setIsVoiceLoaded(true);
        setIsDisclosureLoaded(true);
        setIsServicesLoaded(true);
        setIsKnowledgeLoaded(true);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // ── Save handlers ────────────────────────────────────────────────────
  const saveVoice = async () => {
    if (USE_MOCKS) { setVoiceSaved(voiceDraft); addToast('Voice & persona saved (mock).'); return; }
    try {
      const saved = await api.v2.settings.ai.voice.update(voiceDraft);
      const cfg: VoiceCfg = {
        assistant_name: saved.assistant_name,
        provider_title: saved.provider_title,
        reason_question: saved.reason_question,
        language: saved.language,
      };
      setVoiceSaved(cfg);
      setVoiceDraft(cfg);
      addToast('Voice & persona saved.');
    } catch (e) {
      addToast('Save failed: ' + (e instanceof ApiError ? e.message : 'network error'));
    }
  };
  const discardVoice = () => setVoiceDraft(voiceSaved);

  const saveDisc = async () => {
    if (USE_MOCKS) { setDiscSaved(discDraft); addToast('AI disclosure saved (mock).'); return; }
    try {
      const saved = await api.v2.settings.ai.disclosure.update({
        required: discDraft.ai_disclosure_required,
        phrase: discDraft.ai_disclosure_phrase,
      });
      const cfg: DisclosureCfg = {
        ai_disclosure_required: saved.required,
        ai_disclosure_phrase: saved.phrase,
        last_reviewed_at: saved.last_reviewed_at ?? new Date().toISOString(),
      };
      setDiscSaved(cfg);
      setDiscDraft(cfg);
      addToast('AI disclosure saved.');
    } catch (e) {
      addToast('Save failed: ' + (e instanceof ApiError ? e.message : 'network error'));
    }
  };

  const toggleService = async (id: string) => {
    const next = !(services.find(s => s.id === id)?.bookable);
    // Optimistic update
    setServices(prev => prev.map(s => (s.id === id ? { ...s, bookable: next } : s)));
    if (USE_MOCKS) return;
    const numericId = serviceIdMap[id];
    if (!numericId) return;  // mock-only row
    try {
      await api.v2.settings.ai.servicesBookable.set(numericId, next);
    } catch (e) {
      // Revert on failure
      setServices(prev => prev.map(s => (s.id === id ? { ...s, bookable: !next } : s)));
      addToast('Toggle failed: ' + (e instanceof ApiError ? e.message : 'network error'));
    }
  };

  // ── Clinic Info — controlled state, API-loaded ─────────────────────
  const [clinicCfg, setClinicCfg] = React.useState({
    display_name: 'Oak Dental Calgary',
    address: '1420 17 Ave SW, Calgary, AB T2T 0B9',
    contact_phone: '403-555-0180',
    booking_notification_email: 'frontdesk@oakdentalcalgary.com',
    timezone: 'America/Edmonton',
    working_hour_start: 8,
    working_hour_end: 17,
  });
  React.useEffect(() => {
    if (USE_MOCKS) return;
    api.v2.settings.clinic.get()
      .then(c => {
        setClinicCfg(prev => ({
          ...prev,
          display_name: c.display_name ?? prev.display_name,
          address: c.address ?? prev.address,
          contact_phone: c.contact_phone ?? prev.contact_phone,
          booking_notification_email: c.booking_notification_email ?? prev.booking_notification_email,
          timezone: c.timezone ?? prev.timezone,
          working_hour_start: c.working_hour_start ?? prev.working_hour_start,
          working_hour_end: c.working_hour_end ?? prev.working_hour_end,
        }));
      })
      .catch(() => { /* keep defaults */ });
  }, []);

  const saveAllSettings = async () => {
    if (USE_MOCKS) { addToast('Settings saved (mock).'); return; }
    try {
      await api.v2.settings.clinic.update(clinicCfg);
      addToast('Settings saved.');
    } catch (e) {
      addToast('Save failed: ' + (e instanceof ApiError ? e.message : 'network error'));
    }
  };

  const updateDocBody = async (filename: string, body: string) => {
    setKnowledge(prev => prev.map(d => (d.filename === filename ? { ...d, body } : d)));
    if (USE_MOCKS) return;
    try {
      await api.v2.settings.ai.knowledge.update(filename, { body });
    } catch (e) {
      // Soft-fail: keep local edit but warn.
      console.warn('Knowledge update failed:', e);
    }
  };

  return (
    <>
      <style>{`
        .toggle-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--rr-parchment); }
        .toggle-row:last-child { border-bottom: none; }
        .toggle-label { font-family: var(--font-ui); font-size: .88rem; color: var(--rr-ink); }
        .toggle-sub { font-family: var(--font-ui); font-size: .74rem; color: var(--rr-slate-dark); margin-top: 2px; }
        .int-card { border: 1px solid var(--rr-parchment); border-radius: 6px; padding: 16px 18px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .int-name { font-family: var(--font-ui); font-weight: 600; font-size: .9rem; color: var(--rr-navy-800); }
        .int-desc { font-family: var(--font-ui); font-size: .76rem; color: var(--rr-slate-dark); margin-top: 2px; }
        .toggle-switch { width: 40px; height: 22px; border-radius: 999px; border: none; cursor: pointer; position: relative; transition: background 200ms; }
        .toggle-switch.on { background: var(--rr-navy-800); }
        .toggle-switch.off { background: var(--rr-mist); }
        .toggle-switch::after { content: ''; position: absolute; top: 2px; width: 18px; height: 18px; border-radius: 999px; background: #fff; transition: left 200ms; box-shadow: 0 1px 2px rgba(0,0,0,0.15); }
        .toggle-switch.on::after { left: 20px; }
        .toggle-switch.off::after { left: 2px; }

        /* Shared AI-tab patterns (mirrors design_system prototypes) */
        .ai-overline { font-family: var(--font-ui); font-size: .68rem; font-weight: 700; letter-spacing: .15em; text-transform: uppercase; color: var(--rr-slate-dark); }
        .ai-page-title { font-family: var(--font-display); font-weight: 800; font-size: 1.4rem; color: var(--rr-navy-800); letter-spacing: -.025em; margin: 4px 0 4px; }
        .ai-page-sub { font-family: var(--font-ui); font-size: .9rem; color: var(--rr-slate-dark); max-width: 64ch; line-height: 1.5; margin: 0 0 18px; }
        .ai-panel { background: #fff; border: 1px solid var(--rr-parchment); border-radius: 6px; box-shadow: var(--shadow-xs); overflow: hidden; }
        .ai-panel-pad { padding: 22px 24px; }
        .ai-field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
        .ai-field:last-child { margin-bottom: 0; }
        .ai-lbl { font-family: var(--font-ui); font-size: .82rem; font-weight: 600; color: var(--rr-ink); }
        .ai-lbl-helper { font-family: var(--font-ui); font-size: .76rem; color: var(--rr-slate-dark); }
        .ai-input, .ai-select, .ai-textarea {
          font-family: var(--font-ui); font-size: .9rem; padding: 9px 12px;
          border: 1.5px solid var(--rr-mist); border-radius: 6px;
          width: 100%; box-sizing: border-box; background: #fff; color: var(--rr-ink);
        }
        .ai-textarea { min-height: 84px; resize: vertical; }
        .ai-input:focus, .ai-select:focus, .ai-textarea:focus { border-color: hsl(var(--ring)); outline: none; box-shadow: 0 0 0 3px hsl(var(--primary) / 0.12); }

        .save-bar { background: rgba(255,255,255,0.96); border-top: 1px solid var(--rr-parchment); padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
        .save-bar .left { font-family: var(--font-ui); font-size: .82rem; color: var(--rr-slate-dark); }
        .save-bar .btn-row { display: flex; gap: 10px; align-items: center; }

        .layout-2col { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 20px; align-items: start; }
        @media (max-width: 1100px) { .layout-2col { grid-template-columns: 1fr; } }

        .info-banner { background: #FFF8EC; border: 1px solid #F0E2C8; color: #6B4F1B; font-family: var(--font-ui); font-size: .82rem; padding: 10px 14px; border-radius: 6px; line-height: 1.5; margin-bottom: 14px; }
        .ro-chip { font-family: var(--font-ui); font-size: .62rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: var(--rr-slate-dark); padding: 2px 8px; border-radius: 999px; background: var(--rr-off-white); border: 1px solid var(--rr-parchment); }
        .reviewed-line { font-family: var(--font-mono); font-size: .78rem; color: var(--rr-slate-dark); display: flex; align-items: center; gap: 10px; }
        .char-counter { font-family: var(--font-mono); font-size: .74rem; text-align: right; }
        .char-normal { color: var(--rr-slate-dark); }
        .char-warn { color: #B45309; }
        .char-over { color: #9B2335; }

        /* Services & Disclosure switch — square-edged toggle from prototype */
        .pswitch { position: relative; width: 36px; height: 20px; flex-shrink: 0; display: inline-block; }
        .pswitch input { opacity: 0; width: 0; height: 0; position: absolute; }
        .pswitch-track { position: absolute; inset: 0; background: var(--rr-mist); border-radius: 999px; cursor: pointer; transition: background-color 200ms ease; }
        .pswitch-track::before { content: ''; position: absolute; left: 2px; top: 2px; width: 16px; height: 16px; background: #fff; border-radius: 999px; box-shadow: 0 1px 2px rgba(0,0,0,0.15); transition: transform 200ms ease; }
        .pswitch input:checked + .pswitch-track { background: hsl(var(--primary)); }
        .pswitch input:checked + .pswitch-track::before { transform: translateX(16px); }

        /* Services table */
        .svc-table { width: 100%; border-collapse: collapse; font-family: var(--font-ui); font-size: .88rem; }
        .svc-table th { text-align: left; padding: 12px 16px; font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--rr-slate-dark); border-bottom: 1px solid var(--rr-parchment); }
        .svc-table td { padding: 14px 16px; border-bottom: 1px solid var(--rr-parchment); color: var(--rr-ink); vertical-align: middle; }
        .svc-table tr:last-child td { border-bottom: none; }
        .svc-table .mono { font-family: var(--font-mono); font-size: .82rem; }
        .toggle-cell { display: flex; align-items: center; gap: 8px; }
        .toggle-label-on { font-weight: 500; color: hsl(var(--primary)); font-family: var(--font-ui); font-size: .82rem; }
        .toggle-label-off { font-weight: 500; color: var(--rr-slate-dark); font-family: var(--font-ui); font-size: .82rem; }

        /* Knowledge docs */
        .doc-row { padding: 18px 24px; cursor: pointer; border-bottom: 1px solid var(--rr-parchment); transition: background-color 200ms ease; display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
        .doc-row:last-child { border-bottom: none; }
        .doc-row:hover { background: var(--rr-off-white); }
        .doc-left { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
        .doc-filename { font-family: var(--font-mono); font-size: .82rem; color: var(--rr-slate-dark); }
        .doc-title { font-family: var(--font-display); font-weight: 600; font-size: 1.05rem; color: var(--rr-navy-800); }
        .doc-meta { display: flex; gap: 20px; font-family: var(--font-ui); font-size: .76rem; color: var(--rr-slate-dark); margin-top: 2px; }
        .doc-right { display: flex; align-items: center; flex-shrink: 0; padding-top: 4px; color: var(--rr-slate-dark); }
        .doc-chevron { transition: transform 200ms ease; }
        .doc-chevron.open { transform: rotate(180deg); }
        .doc-expand { padding: 0 24px 18px; border-bottom: 1px solid var(--rr-parchment); }
        .doc-expand:last-child { border-bottom: none; }
        .doc-expand textarea { font-family: var(--font-mono); font-size: .85rem; width: 100%; box-sizing: border-box; min-height: 200px; resize: vertical; padding: 12px; border: 1.5px solid var(--rr-mist); border-radius: 6px; background: #fff; color: var(--rr-ink); line-height: 1.55; }
        .doc-expand textarea:focus { border-color: hsl(var(--ring)); outline: none; box-shadow: 0 0 0 3px hsl(var(--primary) / 0.12); }
      `}</style>

      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-sub">Clinic configuration and system preferences</p>
        </div>
        <button className="btn btn-primary btn-md" onClick={saveAllSettings}>Save changes</button>
      </div>

      <div className="panel" style={{ padding: 0 }}>
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--rr-parchment)', overflowX: 'auto', padding: '0 24px' }}>
          <style>{`
            .stab-btn { background: none; border: none; border-bottom: 2px solid transparent; padding: 10px 16px; font-family: var(--font-ui); font-size: .82rem; font-weight: 500; color: var(--rr-slate-dark); cursor: pointer; white-space: nowrap; }
            .stab-btn.active { color: hsl(var(--primary)); border-bottom-color: hsl(var(--primary)); font-weight: 600; }
          `}</style>
          {TABS.map((t, i) => (
            <button key={t} className={'stab-btn' + (tab === i ? ' active' : '')} onClick={() => setTab(i)}>{t}</button>
          ))}
        </div>
        <div style={{ padding: '24px' }}>

          {/* Tab 0: Clinic Info — controlled, persists via PUT /api/v2/settings/clinic */}
          {tab === 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
              <div>
                <div className="field"><label className="lbl">Display name</label>
                  <input className="d-input" value={clinicCfg.display_name} onChange={e => setClinicCfg({ ...clinicCfg, display_name: e.target.value })} />
                </div>
                <div className="field"><label className="lbl">Address</label>
                  <textarea className="d-textarea" value={clinicCfg.address} onChange={e => setClinicCfg({ ...clinicCfg, address: e.target.value })} />
                </div>
                <div className="field"><label className="lbl">Booking notification email</label>
                  <input className="d-input" value={clinicCfg.booking_notification_email} onChange={e => setClinicCfg({ ...clinicCfg, booking_notification_email: e.target.value })} />
                </div>
              </div>
              <div>
                <div className="field"><label className="lbl">Phone</label>
                  <input className="d-input" value={clinicCfg.contact_phone} onChange={e => setClinicCfg({ ...clinicCfg, contact_phone: e.target.value })} />
                </div>
                <div className="field-row">
                  <div className="field"><label className="lbl">Hour start</label>
                    <input className="d-input" type="number" min={0} max={23} value={clinicCfg.working_hour_start} onChange={e => setClinicCfg({ ...clinicCfg, working_hour_start: Number(e.target.value) || 0 })} />
                  </div>
                  <div className="field"><label className="lbl">Hour end</label>
                    <input className="d-input" type="number" min={0} max={23} value={clinicCfg.working_hour_end} onChange={e => setClinicCfg({ ...clinicCfg, working_hour_end: Number(e.target.value) || 0 })} />
                  </div>
                </div>
                <div className="field"><label className="lbl">Timezone</label>
                  <select className="d-input" value={clinicCfg.timezone} onChange={e => setClinicCfg({ ...clinicCfg, timezone: e.target.value })}>
                    <option>America/Edmonton</option>
                    <option>America/Vancouver</option>
                    <option>America/Toronto</option>
                    <option>America/New_York</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Tab 1: Working Hours */}
          {tab === 1 && (
            <div>
              {DAYS.map(d => (
                <div key={d} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
                  <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '.88rem', width: 100, color: '#1C2333' }}>{d}</span>
                  {d === 'Sunday' ? (
                    <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '.85rem', color: '#8A9BB0' }}>Closed</span>
                  ) : (
                    <>
                      <input type="time" className="d-input" defaultValue={d === 'Saturday' ? '09:00' : '08:00'} style={{ width: 110 }} />
                      <span style={{ color: '#4A5568' }}>–</span>
                      <input type="time" className="d-input" defaultValue={d === 'Saturday' ? '14:00' : '17:00'} style={{ width: 110 }} />
                    </>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Tab 2: Operatories */}
          {tab === 2 && (
            <div>
              <table className="list">
                <thead><tr><th>Name</th><th>Tags</th><th>Status</th></tr></thead>
                <tbody>
                  {[{ name: 'Op 1', tags: ['chair','x-ray'], active: true }, { name: 'Op 2', tags: ['chair','panoramic'], active: true }, { name: 'Op 3', tags: ['chair'], active: false }].map(o => (
                    <tr key={o.name}>
                      <td style={{ fontWeight: 600 }}>{o.name}</td>
                      <td>{o.tags.map((t: string) => <span key={t} className="pill" style={{ background: '#D9EAF5', color: '#2E6494', marginRight: 4 }}>{t}</span>)}</td>
                      <td><span className="pill" style={o.active ? { background: '#E8F5EE', color: '#2A7D4F' } : { background: '#F5F2EC', color: '#4A5568' }}>{o.active ? 'Active' : 'Inactive'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button className="btn btn-ghost btn-sm" style={{ marginTop: 14 }}>+ Add operatory</button>
            </div>
          )}

          {/* Tab 3: Providers */}
          {tab === 3 && (
            <div>
              <table className="list">
                <thead><tr><th>Name</th><th>Title</th><th>Specialty</th><th>Status</th></tr></thead>
                <tbody>
                  {[{ name: 'Dr. Hau Le', title: 'Denturist', specialty: 'Complete dentures' }, { name: 'Dr. Sara Osei', title: 'Dentist', specialty: 'General dentistry' }, { name: 'Dr. Raj Patel', title: 'Hygienist', specialty: 'Periodontics' }].map(p => (
                    <tr key={p.name}>
                      <td style={{ fontWeight: 600 }}>{p.name}</td><td>{p.title}</td><td>{p.specialty}</td>
                      <td><span className="pill" style={{ background: '#E8F5EE', color: '#2A7D4F' }}>Active</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab 4: Users & Roles */}
          {tab === 4 && (
            <table className="list">
              <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
              <tbody>
                {['admin','provider','receptionist'].map((role, i) => {
                  const users = [['Hau Le','hau@oakdental.ca'], ['Sara Osei','sara@oakdental.ca'], ['Mia Tran','mia@oakdental.ca']];
                  const colors: Record<string, string[]> = { admin: ['#D9EAF5','#2E6494'], provider: ['#E8F5EE','#2A7D4F'], receptionist: ['#F5F2EC','#4A5568'] };
                  return (
                    <tr key={role}>
                      <td style={{ fontWeight: 600 }}>{users[i][0]}</td>
                      <td className="id-cell">{users[i][1]}</td>
                      <td><span className="pill" style={{ background: colors[role][0], color: colors[role][1] }}>{role}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}

          {/* Tab 5: Integrations */}
          {tab === 5 && (
            <div>
              {[{ name: 'Twilio SMS', desc: 'Appointment reminders and recall notifications', connected: true },
                { name: 'SendGrid Email', desc: 'Transactional emails and daily summaries', connected: true },
                { name: 'Xero Accounting', desc: 'Invoice sync and payment reconciliation', connected: false },
                { name: 'Google Calendar', desc: 'Two-way calendar sync for providers', connected: false },
              ].map(int => (
                <div key={int.name} className="int-card">
                  <div><div className="int-name">{int.name}</div><div className="int-desc">{int.desc}</div></div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className="pill" style={int.connected ? { background: '#E8F5EE', color: '#2A7D4F' } : { background: '#F5F2EC', color: '#4A5568' }}>{int.connected ? 'Connected' : 'Disconnected'}</span>
                    <button className="btn btn-ghost btn-sm">{int.connected ? 'Configure' : 'Connect'}</button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 6: Notifications */}
          {tab === 6 && (
            <div>
              {[{ label: 'SMS appointment reminders', sub: 'Send SMS 24h before scheduled appointments', on: true },
                { label: 'SMS recall reminders', sub: 'Send SMS when recall window opens', on: true },
                { label: 'Email daily summary', sub: 'Daily digest of appointments and revenue', on: true },
                { label: 'Email weekly report', sub: 'Weekly practice analytics report', on: false },
                { label: 'Email billing alerts', sub: 'Notify on overdue invoices and claim rejections', on: true },
                { label: 'Webhook events', sub: 'Push appointment and invoice events to external URL', on: false },
              ].map(n => (
                <div key={n.label} className="toggle-row">
                  <div><div className="toggle-label">{n.label}</div><div className="toggle-sub">{n.sub}</div></div>
                  <div className={'toggle-switch ' + (n.on ? 'on' : 'off')} />
                </div>
              ))}
            </div>
          )}

          {/* Tab 7: Audit Log */}
          {tab === 7 && (
            <table className="list">
              <thead><tr><th>Action</th><th>Entity</th><th>User</th><th>When</th></tr></thead>
              <tbody>
                {[{ action:'UPDATE',entity:'Patient #P-1042',user:'Hau Le',when:'2026-05-02 14:32' },
                  { action:'CREATE',entity:'Invoice INV-2026-0418',user:'Mia Tran',when:'2026-05-02 11:10' },
                  { action:'DELETE',entity:'Appointment #A-0091',user:'Sara Osei',when:'2026-05-01 09:44' },
                ].map((a, i) => (
                  <tr key={i}>
                    <td><span className="pill" style={{ background: a.action==='UPDATE'?'#F5F2EC':a.action==='CREATE'?'#E8F5EE':'#F8E5E8', color: a.action==='UPDATE'?'#4A5568':a.action==='CREATE'?'#2A7D4F':'#9B2335' }}>{a.action}</span></td>
                    <td>{a.entity}</td><td>{a.user}</td><td className="id-cell">{a.when}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Tab 8: Voice & Persona — mirrors design_system/.../admin-voice.html */}
          {tab === 8 && (
            <div data-testid="voice-panel" data-loaded={isVoiceLoaded ? 'true' : 'false'}>
              <div className="ai-overline">Configuration</div>
              <h2 className="ai-page-title">Voice & persona</h2>
              <p className="ai-page-sub">What the AI calls itself, what it calls your providers, and what it asks for first.</p>

              <div className="layout-2col">
                <form className="ai-panel" onSubmit={e => { e.preventDefault(); saveVoice(); }}>
                  <div className="ai-panel-pad">
                    <label className="ai-field">
                      <span className="ai-lbl">Assistant name</span>
                      <input className="ai-input" maxLength={60} value={voiceDraft.assistant_name} onChange={e => setVoiceDraft({ ...voiceDraft, assistant_name: e.target.value })} />
                      <span className="ai-lbl-helper">This is what the AI says when callers ask “who is this?”</span>
                    </label>
                    <label className="ai-field">
                      <span className="ai-lbl">Provider title</span>
                      <select className="ai-select" value={voiceDraft.provider_title} onChange={e => setVoiceDraft({ ...voiceDraft, provider_title: e.target.value })}>
                        {PROVIDER_TITLES.map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                      <span className="ai-lbl-helper">How the AI refers to the people callers are booking with.</span>
                    </label>
                    <label className="ai-field">
                      <span className="ai-lbl">Reason question</span>
                      <input className="ai-input" maxLength={120} value={voiceDraft.reason_question} onChange={e => setVoiceDraft({ ...voiceDraft, reason_question: e.target.value })} />
                      <span className="ai-lbl-helper">The first question the AI asks after the greeting.</span>
                    </label>
                    <label className="ai-field">
                      <span className="ai-lbl">Language</span>
                      <select className="ai-select" value={voiceDraft.language} onChange={e => setVoiceDraft({ ...voiceDraft, language: e.target.value })}>
                        {LANGUAGES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
                      </select>
                      <span className="ai-lbl-helper">Voice and recognition default. Engineer-managed if you need a custom voice.</span>
                    </label>
                  </div>
                  <div className="save-bar">
                    <span className="left">{voiceDirty ? 'Unsaved changes.' : 'All changes saved.'}</span>
                    <div className="btn-row">
                      {voiceDirty && <button type="button" className="btn btn-ghost btn-md" onClick={discardVoice}>Discard</button>}
                      <button type="submit" className="btn btn-primary btn-md" disabled={!voiceDirty}>Save voice</button>
                    </div>
                  </div>
                </form>

                <aside className="ai-panel ai-panel-pad">
                  <div className="ai-overline">Preview</div>
                  <p className="ai-lbl-helper" style={{ margin: '4px 0 12px' }}>Preview the AI voice with these settings before saving.</p>
                  <button type="button" className="btn btn-ghost btn-md" onClick={() => addToast('Voice preview ready.', voiceDraft.assistant_name)}>Hear it back</button>
                </aside>
              </div>
            </div>
          )}

          {/* Tab 9: AI Disclosure — mirrors design_system/.../admin-disclosure.html */}
          {tab === 9 && (
            <div data-testid="disclosure-panel" data-loaded={isDisclosureLoaded ? 'true' : 'false'}>
              <div className="ai-overline">Configuration</div>
              <h2 className="ai-page-title">AI disclosure</h2>
              <p className="ai-page-sub">When the AI introduces itself.</p>

              <div className="info-banner">When required by law, the AI must say it’s not human at the start of every call.</div>

              <div className="ai-panel">
                <div className="ai-panel-pad">
                  <div className="toggle-row" style={{ borderBottom: '1px solid var(--rr-parchment)' }}>
                    <div>
                      <div className="toggle-label">Disclosure phrase required at the start of every AI call</div>
                      <div className="toggle-sub">If your jurisdiction requires AI disclosure, leave this on.</div>
                    </div>
                    <label className="pswitch">
                      <input type="checkbox" checked={discDraft.ai_disclosure_required} onChange={e => setDiscDraft({ ...discDraft, ai_disclosure_required: e.target.checked })} aria-label="Disclosure phrase required" />
                      <span className="pswitch-track" />
                    </label>
                  </div>

                  <div className="ai-field" style={{ marginTop: 16 }}>
                    <span className="ai-lbl">Disclosure phrase</span>
                    <textarea className="ai-textarea" value={discDraft.ai_disclosure_phrase} maxLength={400} onChange={e => setDiscDraft({ ...discDraft, ai_disclosure_phrase: e.target.value })} />
                    <span className={'char-counter ' + discCharClass}>{discCharLen} / 280 characters</span>
                    <span className="ai-lbl-helper">This is the first sentence the AI says when it picks up. Keep it short and clear.</span>
                  </div>

                  <div className="reviewed-line" style={{ marginTop: 8 }}>
                    <span>Last reviewed: {discReviewedDate}</span>
                    <span className="ro-chip">Engineer-managed</span>
                  </div>
                </div>
                <div className="save-bar">
                  <span className="left">{discDirty ? 'Unsaved changes.' : 'All changes saved.'}</span>
                  <div className="btn-row">
                    {discDirty && <button type="button" className="btn btn-ghost btn-md" onClick={() => setDiscDraft(discSaved)}>Discard</button>}
                    <button type="button" className="btn btn-primary btn-md" disabled={!discDirty} onClick={saveDisc}>Save disclosure</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab 10: Services — mirrors design_system/.../admin-services.html */}
          {tab === 10 && (
            <div data-testid="services-panel" data-loaded={isServicesLoaded ? 'true' : 'false'}>
              <div className="ai-overline">Configuration</div>
              <h2 className="ai-page-title">The Service catalogue</h2>
              <p className="ai-page-sub">Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only.</p>

              <div className="ai-panel">
                <table className="svc-table">
                  <thead>
                    <tr>
                      <th>Service ID</th>
                      <th>Name</th>
                      <th>Duration</th>
                      <th>Base price</th>
                      <th>AI Bookable</th>
                    </tr>
                  </thead>
                  <tbody>
                    {services.map(svc => (
                      <tr key={svc.id}>
                        <td className="mono">{svc.id}</td>
                        <td>{svc.name}</td>
                        <td>{svc.duration_min} min</td>
                        <td className="mono">{fmtPrice(svc.base_price)}</td>
                        <td>
                          <div className="toggle-cell">
                            <label className="pswitch">
                              <input type="checkbox" checked={svc.bookable} onChange={() => toggleService(svc.id)} aria-label={`Toggle AI bookable for ${svc.name}`} />
                              <span className="pswitch-track" />
                            </label>
                            <span className={svc.bookable ? 'toggle-label-on' : 'toggle-label-off'}>{svc.bookable ? 'AI Bookable' : 'Front-desk only'}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="save-bar" style={{ justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-primary btn-md" onClick={() => addToast('Service catalogue saved.')}>Save service catalogue</button>
                </div>
              </div>
            </div>
          )}

          {/* Tab 11: Knowledge — mirrors design_system/.../admin-knowledge.html */}
          {tab === 11 && (
            <div data-testid="knowledge-panel" data-loaded={isKnowledgeLoaded ? 'true' : 'false'}>
              <div className="ai-overline">Configuration</div>
              <h2 className="ai-page-title">The Knowledge base</h2>
              <p className="ai-page-sub">Edit the AI knowledge base. The AI uses these files as ground truth when answering caller questions.</p>

              <div className="ai-panel">
                {knowledge.length === 0 ? (
                  <div style={{ padding: '40px 24px', textAlign: 'center', fontFamily: 'var(--font-ui)', fontSize: '.9rem', color: 'var(--rr-slate-dark)', lineHeight: 1.5 }}>
                    No knowledge yet. Drop a markdown file in to give the agent something to draw on.
                  </div>
                ) : (
                  knowledge.map(doc => {
                    const open = !!openDocs[doc.filename];
                    return (
                      <div key={doc.filename}>
                        <div className="doc-row" onClick={() => toggleDoc(doc.filename)} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleDoc(doc.filename); } }}>
                          <div className="doc-left">
                            <span className="doc-filename">{doc.filename}</span>
                            <span className="doc-title">{doc.title}</span>
                            <div className="doc-meta">
                              <span>Last updated: {doc.last_updated}</span>
                              <span>Word count: {doc.word_count}</span>
                            </div>
                          </div>
                          <div className="doc-right">
                            <svg className={'doc-chevron' + (open ? ' open' : '')} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="6 9 12 15 18 9" /></svg>
                          </div>
                        </div>
                        {open && (
                          <div className="doc-expand">
                            <textarea value={doc.body} onChange={e => updateDocBody(doc.filename, e.target.value)} aria-label={`Content of ${doc.filename}`} />
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
                <div className="save-bar" style={{ justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-primary btn-md" onClick={() => addToast('Knowledge updates saved.')}>Save knowledge updates</button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: "'Inter', sans-serif", fontSize: '.72rem', color: 'var(--rr-slate)', letterSpacing: '.06em' }}>
        ROCKYRIDGE · DENTAL AI · v1
      </div>
    </>
  );
}
