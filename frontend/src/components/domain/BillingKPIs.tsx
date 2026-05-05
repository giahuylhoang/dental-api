export function BillingKPIs() {
  return (
    <div className="kpi-row">
      <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: '20px 22px', boxShadow: '0 1px 2px rgba(10,25,47,0.06)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.68rem', fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#3A7FBD' }}>Total Revenue</span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '2rem', fontWeight: 600, color: '#0A192F', letterSpacing: '-0.02em', lineHeight: 1.1 }}>$14.6K</span>
        <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: '0.78rem', color: '#2A7D4F', fontWeight: 500 }}>▲ + 8.2% <span style={{ color: '#8A9BB0', fontWeight: 400 }}>vs last month</span></span>
      </div>
      <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: '20px 22px', boxShadow: '0 1px 2px rgba(10,25,47,0.06)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.68rem', fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#3A7FBD' }}>Outstanding</span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '2rem', fontWeight: 600, color: '#0A192F', letterSpacing: '-0.02em', lineHeight: 1.1 }}>$4.2K</span>
        <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: '0.78rem', color: '#9B2335', fontWeight: 500 }}>▼ + 2.1% <span style={{ color: '#8A9BB0', fontWeight: 400 }}>vs last month</span></span>
      </div>
      <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: '20px 22px', boxShadow: '0 1px 2px rgba(10,25,47,0.06)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.68rem', fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#0A192F' }}>Claims Pending</span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '2rem', fontWeight: 600, color: '#0A192F', letterSpacing: '-0.02em', lineHeight: 1.1 }}>12</span>
        <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: '0.78rem', color: '#4A5568', fontWeight: 500 }}>· – 3 <span style={{ color: '#8A9BB0', fontWeight: 400 }}>vs last week</span></span>
      </div>
      <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: '20px 22px', boxShadow: '0 1px 2px rgba(10,25,47,0.06)', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.68rem', fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#3A7FBD' }}>Collection Rate</span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '2rem', fontWeight: 600, color: '#0A192F', letterSpacing: '-0.02em', lineHeight: 1.1 }}>84%</span>
        <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: '0.78rem', color: '#2A7D4F', fontWeight: 500 }}>▲ + 1.5% <span style={{ color: '#8A9BB0', fontWeight: 400 }}>vs last month</span></span>
      </div>
    </div>
  );
}
