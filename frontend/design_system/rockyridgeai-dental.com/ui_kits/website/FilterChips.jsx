// FilterChips — pill-row filter bar
const FilterChips = ({ chips, active, onChange }) => (
  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
    {chips.map(chip => (
      <button
        key={chip.key}
        onClick={() => onChange(chip.key)}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          height: 32, padding: '0 12px', borderRadius: '999px',
          border: chip.key === active ? '1px solid var(--rr-steel-200)' : '1px solid var(--rr-parchment)',
          background: chip.key === active ? 'var(--rr-mist)' : '#fff',
          fontFamily: 'var(--font-ui)', fontSize: '.76rem',
          color: chip.key === active ? 'var(--rr-navy-800)' : 'var(--rr-slate-dark)',
          fontWeight: chip.key === active ? 600 : 400,
          cursor: 'pointer',
        }}
      >
        {chip.label}
        {chip.count != null && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '.68rem' }}>{chip.count}</span>
        )}
      </button>
    ))}
  </div>
);

window.FilterChips = FilterChips;
