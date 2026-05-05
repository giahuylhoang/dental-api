'use client';

interface KpiTileProps {
  label: string;
  value: string | number;
  delta?: string;
  trend?: 'up' | 'down' | 'neutral';
  accent?: 'steel' | 'navy';
  href?: string;
  onClick?: () => void;
}

export function KpiTile({ label, value, delta, trend = 'up', accent = 'steel', onClick }: KpiTileProps) {
  const accentColor = accent === 'navy' ? '#0A192F' : '#3A7FBD';
  const dColor = trend === 'up' ? '#2A7D4F' : trend === 'down' ? '#9B2335' : '#4A5568';
  const arrow = trend === 'up' ? '▲' : trend === 'down' ? '▼' : '·';

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  return (
    <div
      onClick={handleClick}
      style={{
        background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6,
        padding: '20px 22px', boxShadow: '0 1px 2px rgba(10,25,47,0.06)',
        display: 'flex', flexDirection: 'column', gap: 6,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'box-shadow 200ms ease, border-color 200ms ease',
      }}
      onMouseEnter={e => { if (onClick) e.currentTarget.style.boxShadow = '0 4px 20px rgba(10,25,47,0.12)'; }}
      onMouseLeave={e => { if (onClick) e.currentTarget.style.boxShadow = '0 1px 2px rgba(10,25,47,0.06)'; }}
    >
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
}
