// KpiTile.jsx — Dashboard KPI tile (label + big mono number + optional delta)

const KpiTile = ({ label, value, delta, trend = 'up', accent = 'steel' }) => {
  const accentColor = accent === 'navy' ? '#0A192F' : '#3A7FBD';
  const dColor = trend === 'up' ? '#2A7D4F' : trend === 'down' ? '#9B2335' : '#4A5568';
  const arrow = trend === 'up' ? '▲' : trend === 'down' ? '▼' : '·';
  return (
    <div style={{
      background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6,
      padding: '20px 22px', boxShadow: '0 1px 2px rgba(10,25,47,0.06)',
      display: 'flex', flexDirection: 'column', gap: 6,
    }}>
      <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.68rem', fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: accentColor }}>
        {label}
      </span>
      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '2rem', fontWeight: 600, color: '#0A192F', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
        {value}
      </span>
      {delta != null && (
        <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: '0.78rem', color: dColor, fontWeight: 500 }}>
          <span>{arrow}</span><span>{delta}</span>
          <span style={{ color: '#8A9BB0', fontWeight: 400 }}>vs last week</span>
        </span>
      )}
    </div>
  );
};

Object.assign(window, { KpiTile });
