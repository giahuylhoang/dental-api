// Philosophy.jsx — Brand philosophy / clinical operations thinking

const Philosophy = () => (
  <section style={{ background: '#0A192F', padding: '96px 48px', position: 'relative', overflow: 'hidden' }}>
    <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', opacity: 0.03 }}>
      <div style={{ position: 'absolute', top: '20%', left: '-5%', width: '60%', height: '60%', border: '1px solid #E0E0E0', transform: 'rotate(8deg)' }} />
    </div>
    <div style={{ maxWidth: 1200, margin: '0 auto', position: 'relative', zIndex: 1 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center' }}>
        <div>
          <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#3A7FBD', marginBottom: 24 }}>
            Our Philosophy
          </div>
          <blockquote style={{ margin: 0, padding: '0 0 0 28px', borderLeft: '3px solid #3A7FBD' }}>
            <p style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontStyle: 'italic', fontSize: 'clamp(1.4rem, 2.5vw, 2rem)', lineHeight: 1.3, color: '#FAF9F6', margin: 0 }}>
              "Open the chart. The history is already there."
            </p>
          </blockquote>
          <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '1rem', lineHeight: 1.75, color: 'rgba(250,249,246,0.55)', marginTop: 28, maxWidth: 480 }}>
            Clinical operations are too important to be held together by spreadsheets and email. Every screen in Rockyridge Dental AI assumes the operator is mid-shift, the patient is in the chair, and the answer needs to be one click away.
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {[
            { title: 'Clinical Precision', body: 'Every workflow is treated like a procedure — predictable, audited, and reviewable. We measure twice, save once.' },
            { title: 'Sovereign Ownership', body: 'Your patient data, your schedule, your reports — all live in your tenancy. We export, we never lock in.' },
            { title: 'One Connected System', body: 'Schedule, chart, lab, billing, insurance — one engine. No double-entry. No drift. No lost recalls.' },
          ].map((item, i) => (
            <div key={item.title} style={{
              padding: '28px 0',
              borderBottom: i < 2 ? '1px solid rgba(255,255,255,0.08)' : 'none',
              display: 'flex', gap: 20, alignItems: 'flex-start',
            }}>
              <span style={{
                fontFamily: "'Montserrat', sans-serif", fontWeight: 900,
                fontSize: '1.5rem', lineHeight: 1, letterSpacing: '-0.04em',
                color: 'rgba(58,127,189,0.25)', flexShrink: 0, width: 32,
              }}>0{i + 1}</span>
              <div>
                <div style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1.05rem', color: '#FAF9F6', marginBottom: 8, letterSpacing: '-0.01em' }}>{item.title}</div>
                <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.9rem', lineHeight: 1.7, color: 'rgba(250,249,246,0.55)' }}>{item.body}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </section>
);

Object.assign(window, { Philosophy });
