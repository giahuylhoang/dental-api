// FormField — labelled input wrapper
const FormField = ({ label, hint, error, children }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 14 }}>
    <label style={{
      fontFamily: 'var(--font-ui)', fontSize: '.72rem', fontWeight: 500,
      color: error ? '#9B2335' : 'var(--rr-ink)',
      letterSpacing: '.06em', textTransform: 'uppercase',
    }}>
      {label}
    </label>
    {children}
    {hint && !error && (
      <span style={{ fontFamily: 'var(--font-ui)', fontSize: '.72rem', color: 'var(--rr-slate-dark)' }}>{hint}</span>
    )}
    {error && (
      <span style={{ fontFamily: 'var(--font-ui)', fontSize: '.72rem', color: '#9B2335' }}>{error}</span>
    )}
  </div>
);

window.FormField = FormField;
