// SearchInput — search field with embedded magnifier icon
const SearchInput = ({ value, onChange, placeholder }) => (
  <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
    <svg
      width="14" height="14" viewBox="0 0 24 24" fill="none"
      stroke="#8A9BB0" strokeWidth="1.6"
      style={{ position: 'absolute', left: 12, pointerEvents: 'none' }}
    >
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
    <input
      type="text"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder || 'Search…'}
      style={{
        height: 36, padding: '0 12px 0 36px', borderRadius: 4,
        border: '1px solid var(--rr-parchment)', background: 'var(--rr-warm-white)',
        fontFamily: 'var(--font-ui)', fontSize: '.85rem', color: 'var(--rr-ink)',
        outline: 'none', minWidth: 220,
      }}
    />
  </div>
);

window.SearchInput = SearchInput;
