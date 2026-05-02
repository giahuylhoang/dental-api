// KpiTile.tsx — dental-pms.v1 reference layout
// Demonstrates: --shadow-sm, --radius-lg, --color-success, --color-warning,
//               --color-danger, --text-3xl, --text-sm, --space-*

type Trend = 'up' | 'down' | 'neutral';

interface KpiTileProps {
  label: string;
  value: string | number;
  trend?: Trend;
  trendLabel?: string;
  accent?: 'success' | 'warning' | 'danger' | 'action';
}

const ACCENT_COLOR: Record<string, string> = {
  success: 'var(--color-success)',
  warning: 'var(--color-warning)',
  danger:  'var(--color-danger)',
  action:  'var(--color-action)',
};

export function KpiTile({ label, value, trend = 'neutral', trendLabel, accent = 'action' }: KpiTileProps) {
  const trendColor = trend === 'up' ? 'var(--color-success)' : trend === 'down' ? 'var(--color-danger)' : 'var(--color-text-secondary)';
  const trendIcon  = trend === 'up' ? '↑' : trend === 'down' ? '↓' : '—';

  return (
    <div style={{
      background: 'white',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border-subtle)',
      boxShadow: 'var(--shadow-sm)',
      padding: 'var(--space-5) var(--space-6)',
      fontFamily: 'var(--font-display)',
      minWidth: 160,
    }}>
      <div style={{ fontSize: 'var(--text-xs)', fontWeight: 500, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)', marginBottom: 'var(--space-2)' }}>
        {label}
      </div>
      <div style={{ fontSize: 'var(--text-3xl)', fontWeight: 700, color: ACCENT_COLOR[accent], lineHeight: 'var(--leading-tight)' }}>
        {value}
      </div>
      {trendLabel && (
        <div style={{ fontSize: 'var(--text-xs)', color: trendColor, marginTop: 'var(--space-2)' }}>
          {trendIcon} {trendLabel}
        </div>
      )}
    </div>
  );
}
