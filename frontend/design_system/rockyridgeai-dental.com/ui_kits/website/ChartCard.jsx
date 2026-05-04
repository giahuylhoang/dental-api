// ChartCard — KPI card with title, big number, optional sparkline
const ChartCard = ({ title, value, delta, trend, unit }) => {
  const sparkline = trend && trend.length > 1 ? (() => {
    const W = 80, H = 28;
    const min = Math.min(...trend), max = Math.max(...trend);
    const range = max - min || 1;
    const pts = trend.map((v, i) => {
      const x = (i / (trend.length - 1)) * W;
      const y = H - ((v - min) / range) * H;
      return `${x},${y}`;
    }).join(' ');
    return (
      <svg width={W} height={H} style={{ display: 'block' }}>
        <polyline points={pts} fill="none" stroke="hsl(var(--primary))" strokeWidth="1.5" strokeLinejoin="round"/>
      </svg>
    );
  })() : null;

  const deltaColor = delta > 0 ? '#2A7D4F' : delta < 0 ? '#9B2335' : 'var(--rr-slate-dark)';
  const deltaSign = delta > 0 ? '+' : '';

  return (
    <div style={{
      background: '#fff', border: '1px solid var(--rr-parchment)', borderRadius: 6,
      padding: '18px 20px', boxShadow: 'var(--shadow-xs)',
      display: 'flex', flexDirection: 'column', gap: 6,
    }}>
      <div style={{ fontFamily: 'var(--font-ui)', fontSize: '.72rem', fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--rr-slate-dark)' }}>
        {title}
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 8 }}>
        <div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.8rem', color: 'var(--rr-navy-800)', letterSpacing: '-.025em' }}>
            {value}
          </span>
          {unit && <span style={{ fontFamily: 'var(--font-ui)', fontSize: '.82rem', color: 'var(--rr-slate-dark)', marginLeft: 4 }}>{unit}</span>}
          {delta != null && (
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: '.76rem', color: deltaColor, marginTop: 2 }}>
              {deltaSign}{delta}%
            </div>
          )}
        </div>
        {sparkline}
      </div>
    </div>
  );
};

window.ChartCard = ChartCard;
