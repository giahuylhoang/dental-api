// Tabs — horizontal tab strip with optional counts
const Tabs = ({ tabs, active, onChange }) => (
  <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--rr-parchment)' }}>
    {tabs.map(tab => (
      <button
        key={tab.key}
        onClick={() => onChange(tab.key)}
        style={{
          background: 'none', border: 'none',
          borderBottom: tab.key === active ? '2px solid var(--rr-navy-800)' : '2px solid transparent',
          padding: '10px 16px',
          fontFamily: 'var(--font-ui)', fontSize: '.82rem',
          fontWeight: tab.key === active ? 600 : 500,
          color: tab.key === active ? 'var(--rr-navy-800)' : 'var(--rr-slate-dark)',
          cursor: 'pointer', whiteSpace: 'nowrap',
        }}
      >
        {tab.label}
        {tab.count != null && (
          <span style={{
            marginLeft: 6, fontSize: '.7rem', fontFamily: 'var(--font-mono)',
            background: 'var(--rr-mist)', color: 'var(--rr-steel-700)',
            padding: '1px 7px', borderRadius: '999px', fontWeight: 600,
          }}>
            {tab.count}
          </span>
        )}
      </button>
    ))}
  </div>
);

window.Tabs = Tabs;
