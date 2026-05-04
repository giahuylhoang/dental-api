// EmptyState.jsx — Standard empty state (icon + title + body + CTA)

const EmptyState = ({ icon, title, body, ctaLabel, onCta }) => (
  <div style={{
    background: '#fff', border: '1px dashed #C8CCCC', borderRadius: 6,
    padding: '40px 32px', display: 'flex', flexDirection: 'column', alignItems: 'center',
    gap: 12, textAlign: 'center', color: '#4A5568',
  }}>
    <div style={{ width: 48, height: 48, borderRadius: 999, background: '#F5F2EC', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#3A7FBD' }}>
      {icon || (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      )}
    </div>
    <div style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1.05rem', color: '#0A192F' }}>{title}</div>
    <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.85rem', maxWidth: 360, lineHeight: 1.6 }}>{body}</div>
    {ctaLabel && (
      <button className="btn btn-primary btn-md" style={{ marginTop: 6 }} onClick={onCta}>{ctaLabel}</button>
    )}
  </div>
);

Object.assign(window, { EmptyState });
