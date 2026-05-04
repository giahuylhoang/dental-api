// Drawer — right-side slide-over panel
const Drawer = ({ open, onClose, title, width, children }) => {
  React.useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  if (!open) return null;

  const w = width || 'min(560px, 100%)';

  return (
    <React.Fragment>
      <div
        style={{ position: 'fixed', inset: 0, background: 'rgba(10,25,47,0.4)', zIndex: 40 }}
        onClick={onClose}
      />
      <div style={{
        position: 'fixed', top: 0, bottom: 0, right: 0, width: w,
        background: '#fff', boxShadow: 'var(--shadow-xl)',
        display: 'flex', flexDirection: 'column', zIndex: 50,
        animation: 'rrDrawerIn 350ms cubic-bezier(0.16,1,0.3,1)',
      }}>
        <style>{`@keyframes rrDrawerIn { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>
        <div style={{
          padding: '22px 28px', borderBottom: '1px solid var(--rr-parchment)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16,
        }}>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.4rem', color: 'var(--rr-navy-800)', letterSpacing: '-.02em' }}>
            {title}
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 6, color: 'var(--rr-slate-dark)', borderRadius: 4 }}
            aria-label="Close"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div style={{ flex: 1, padding: '22px 28px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 18 }}>
          {children}
        </div>
      </div>
    </React.Fragment>
  );
};

window.Drawer = Drawer;
