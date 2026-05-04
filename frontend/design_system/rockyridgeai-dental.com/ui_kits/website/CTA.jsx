// CTA.jsx + Footer.jsx — schedule-a-demo section + marketing footer

const CTA = ({ onNav }) => (
  <section id="contact" style={{ background: '#F5F2EC', padding: '96px 48px', borderTop: '1px solid #EDE9E0' }}>
    <div style={{ maxWidth: 1200, margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center' }}>
      <div>
        <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#3A7FBD', marginBottom: 16 }}>
          Begin the Engagement
        </div>
        <h2 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: 'clamp(1.8rem, 3vw, 2.5rem)', letterSpacing: '-0.03em', lineHeight: 1.15, color: '#0A192F', margin: '0 0 20px' }}>
          Schedule a 30-minute demo
        </h2>
        <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '1rem', lineHeight: 1.75, color: '#3D4D61', margin: 0, maxWidth: 420 }}>
          Walk one of your real workflows on Rockyridge Dental AI. We'll set up a sandbox with your typical schedule and run through schedule, chart, and lab side-by-side.
        </p>
        <div style={{ display: 'flex', gap: 16, marginTop: 32 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.8rem', color: '#0A192F' }}>No obligation</span>
            <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.78rem', color: '#4A5568' }}>Operations review, not a sales call</span>
          </div>
        </div>
      </div>
      <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: 36, boxShadow: '0 4px 20px rgba(10,25,47,0.08)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            {[['Full Name', 'Dr Hau Le'], ['Clinic', 'Oak Dental Calgary']].map(([lbl, ph]) => (
              <div key={lbl} style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                <label style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.78rem', color: '#1C2333' }}>{lbl}</label>
                <input readOnly placeholder={ph} style={{
                  fontFamily: "'Inter', sans-serif", fontSize: '0.875rem', color: '#1C2333',
                  background: '#FAF9F6', border: '1.5px solid #C8CCCC', borderRadius: 6,
                  padding: '9px 12px', outline: 'none',
                }} />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            <label style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.78rem', color: '#1C2333' }}>Practice size</label>
            <select style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.875rem', color: '#1C2333', background: '#FAF9F6', border: '1.5px solid #C8CCCC', borderRadius: 6, padding: '9px 12px', outline: 'none' }}>
              <option>1 location · 1–3 chairs</option>
              <option>1 location · 4–8 chairs</option>
              <option>2–3 locations</option>
              <option>4+ locations / DSO</option>
            </select>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            <label style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.78rem', color: '#1C2333' }}>What's the operations gap?</label>
            <textarea rows={3} readOnly placeholder="Where is the schedule / chart / lab leaking time?" style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.875rem', color: '#1C2333', background: '#FAF9F6', border: '1.5px solid #C8CCCC', borderRadius: 6, padding: '9px 12px', outline: 'none', resize: 'vertical' }} />
          </div>
          <button className="btn btn-navy btn-lg" style={{ marginTop: 4 }}>Request a demo</button>
        </div>
      </div>
    </div>
  </section>
);

const Footer = () => (
  <footer style={{ background: '#060F1E', padding: '56px 48px 36px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 48, paddingBottom: 40, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src="../../assets/RR_logo_white.svg" alt="Rockyridge Dental AI" style={{ height: 28 }} />
            <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.05 }}>
              <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: '0.88rem', color: '#FAF9F6', letterSpacing: '0.08em' }}>ROCKYRIDGE</span>
              <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 400, fontSize: '0.7rem', color: 'rgba(250,249,246,0.6)', letterSpacing: 1.4 }}>DENTAL AI</span>
            </div>
          </div>
          <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.875rem', lineHeight: 1.7, color: 'rgba(250,249,246,0.4)', margin: 0, maxWidth: 280 }}>
            A vertical product of Rockyridge AI Solutions. Schedules · Charts · Labs · Practices.
          </p>
        </div>
        {[
          { heading: 'Product', links: [
            { label: 'Schedule',   href: 'index.html#schedule'  },
            { label: 'Chart',      href: 'index.html#chart'     },
            { label: 'Lab',        href: 'index.html#lab'       },
            { label: 'Insurance',  href: 'index.html#services'  },
            { label: 'Reporting',  href: 'index.html#services'  },
          ]},
          { heading: 'Company', links: [
            { label: 'About',      href: 'index.html#intelligence' },
            { label: 'Philosophy', href: 'index.html#intelligence' },
            { label: 'Pricing',    href: 'index.html#pricing'      },
            { label: 'Contact',    href: 'index.html#contact'      },
          ]},
          { heading: 'Connect', links: [
            { label: 'Documentation', href: 'index.html#contact' },
            { label: 'Email Us',      href: 'index.html#contact' },
            { label: 'Privacy',       href: 'index.html#legal'   },
            { label: 'Terms',         href: 'index.html#legal'   },
          ]},
        ].map(col => (
          <div key={col.heading} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#3A7FBD' }}>{col.heading}</div>
            {col.links.map(l => (
              <a key={l.label} href={l.href} style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', color: 'rgba(250,249,246,0.45)', textDecoration: 'none' }}>{l.label}</a>
            ))}
          </div>
        ))}
      </div>
      <div style={{ paddingTop: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.78rem', color: 'rgba(250,249,246,0.25)' }}>© 2026 Rockyridge AI Solutions. All rights reserved.</span>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.72rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(250,249,246,0.2)' }}>Schedule · Chart · Lab · Sovereign</span>
      </div>
    </div>
  </footer>
);

Object.assign(window, { CTA, Footer });
