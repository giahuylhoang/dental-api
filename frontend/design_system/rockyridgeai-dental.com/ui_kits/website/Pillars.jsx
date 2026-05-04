// Pillars.jsx — Three pillars of Rockyridge Dental AI: Schedule · Chart · Lab.

const PILLARS = [
  {
    number: '01', label: 'The Schedule',
    title: 'Operatory at a glance',
    desc: 'Real-time chair-by-chair availability across operatories, providers, and recall windows. Drag to reschedule with automated patient SMS — conflicts flagged before save.',
    items: ['Per-clinic working hours · holidays · rotations', 'Drag-to-reschedule with SMS reminders', 'Recall windows surfaced before they go stale', 'Sovereign export to ICS / CSV / your PMS'],
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
      </svg>
    ),
  },
  {
    number: '02', label: 'The Chart',
    title: 'One screen, always in sync',
    desc: 'Tooth-level history, treatment plans, lab cases, insurance, and clinical notes — never duplicated across systems, never out of sync. Open a chart, and the history is already there.',
    items: ['Tooth-level history · 32-tooth chart', 'Treatment plans · accepted, in-flight, completed', 'Insurance verification · claim auto-submission', 'Audit log on every clinical edit'],
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>
      </svg>
    ),
  },
  {
    number: '03', label: 'The Lab',
    title: 'Every case, end to end',
    desc: 'Track lab cases from impression to seat. Vendor SLAs, materials, lot numbers, and patient ETAs — all in one queue with status changes broadcast to the clinical chart.',
    items: ['Vendor SLAs · materials · lot tracking', 'Status broadcast to chair-side chart', 'Patient ETA on the appointment', 'Late-case alerts surfaced in the schedule'],
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10 2v7.31"/><path d="M14 9.3V1.99"/><path d="M8.5 2h7"/><path d="M14 9.3a6.5 6.5 0 1 1-4 0"/><path d="M5.52 16h12.96"/>
      </svg>
    ),
  },
];

const Pillars = () => (
  <section id="services" style={{ background: '#FAF9F6', padding: '96px 48px' }}>
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: 64, maxWidth: 600 }}>
        <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#3A7FBD', marginBottom: 16 }}>
          The Three-Pillar System
        </div>
        <h2 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: 'clamp(1.8rem, 3.5vw, 2.8rem)', letterSpacing: '-0.03em', lineHeight: 1.15, color: '#0A192F', margin: 0 }}>
          Schedule · Chart · Lab
        </h2>
        <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '1.05rem', lineHeight: 1.75, color: '#3D4D61', marginTop: 16, maxWidth: 520 }}>
          Three pillars, one connected system. Patient histories never duplicate. Lab cases never go stale. Insurance never gets dropped. The platform is one engine — not seven point tools held together with email.
        </p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
        {PILLARS.map((p, i) => (
          <div key={p.number} style={{
            background: i === 1 ? '#0A192F' : '#fff',
            border: i === 1 ? 'none' : '1px solid #EDE9E0',
            borderRadius: 6, padding: 36,
            boxShadow: i === 1 ? '0 8px 40px rgba(10,25,47,0.18)' : '0 2px 8px rgba(10,25,47,0.06)',
            display: 'flex', flexDirection: 'column', gap: 20,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 900, fontSize: '3rem', lineHeight: 1, color: i === 1 ? 'rgba(255,255,255,0.08)' : 'rgba(10,25,47,0.06)', letterSpacing: '-0.04em' }}>{p.number}</span>
              <span style={{ color: '#3A7FBD', marginTop: 4 }}>{p.icon}</span>
            </div>
            <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.68rem', letterSpacing: '0.14em', textTransform: 'uppercase', color: i === 1 ? '#8A9BB0' : '#3A7FBD' }}>{p.label}</div>
            <div style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1.2rem', letterSpacing: '-0.02em', lineHeight: 1.25, color: i === 1 ? '#FAF9F6' : '#0A192F' }}>{p.title}</div>
            <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.9rem', lineHeight: 1.7, color: i === 1 ? 'rgba(250,249,246,0.6)' : '#3D4D61', margin: 0 }}>{p.desc}</p>
            <div style={{ height: 1, background: i === 1 ? 'rgba(255,255,255,0.08)' : '#EDE9E0' }} />
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {p.items.map(item => (
                <li key={item} style={{ display: 'flex', alignItems: 'center', gap: 10, fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', color: i === 1 ? 'rgba(250,249,246,0.7)' : '#3D4D61' }}>
                  <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#3A7FBD', flexShrink: 0 }} />{item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  </section>
);

Object.assign(window, { Pillars });
