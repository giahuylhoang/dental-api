// ToothChartTile.jsx — Compact 32-tooth chart (FDI numbering) with status fills.

const TOOTH_STATUS = {
  sound: { fill: '#fff', stroke: '#C8CCCC' },
  caries:{ fill: '#FDF3E5', stroke: '#B45309' },
  resto: { fill: '#D9EAF5', stroke: '#3A7FBD' },
  crown: { fill: '#A8CCE8', stroke: '#2E6494' },
  miss:  { fill: '#EDE9E0', stroke: '#8A9BB0' },
  endo:  { fill: '#F8E5E8', stroke: '#9B2335' },
};

// Sample marking — by tooth number (FDI quadrants 11–48, primary teeth omitted).
const MARKINGS = {
  16: 'resto', 17: 'caries', 26: 'crown', 27: 'resto',
  36: 'crown', 37: 'caries', 46: 'resto', 47: 'sound',
  31: 'sound', 41: 'sound', 11: 'sound',  21: 'sound',
  18: 'miss',  28: 'miss',  38: 'miss',  48: 'miss',
};

const ToothChartTile = () => {
  const upper = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lower = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  const Tooth = ({ n }) => {
    const st = MARKINGS[n] || 'sound';
    const tone = TOOTH_STATUS[st];
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <div style={{
          width: 22, height: 28, borderRadius: '6px 6px 3px 3px',
          background: tone.fill, border: `1.5px solid ${tone.stroke}`,
        }}/>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.6rem', color: '#8A9BB0' }}>{n}</span>
      </div>
    );
  };

  return (
    <div style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: 18, boxShadow: '0 1px 2px rgba(10,25,47,0.06)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '0.9rem', color: '#0A192F' }}>Tooth chart</span>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.7rem', color: '#8A9BB0' }}>FDI · Updated 2026-04-21</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(16, 1fr)', gap: 4, marginBottom: 8 }}>
        {upper.map(n => <Tooth key={n} n={n} />)}
      </div>
      <div style={{ height: 1, background: '#EDE9E0', margin: '8px 0' }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(16, 1fr)', gap: 4 }}>
        {lower.map(n => <Tooth key={n} n={n} />)}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 14, fontFamily: "'Inter', sans-serif", fontSize: '0.7rem', color: '#4A5568' }}>
        {Object.entries(TOOTH_STATUS).map(([k, t]) => (
          <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: t.fill, border: `1px solid ${t.stroke}` }} /> {k}
          </span>
        ))}
      </div>
    </div>
  );
};

Object.assign(window, { ToothChartTile });
