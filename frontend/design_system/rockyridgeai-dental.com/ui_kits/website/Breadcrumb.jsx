// Breadcrumb — navigation breadcrumb trail
const Breadcrumb = ({ items }) => (
  <nav style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-ui)', fontSize: '.82rem' }}>
    {items.map((item, i) => {
      const isLast = i === items.length - 1;
      return (
        <React.Fragment key={i}>
          {i > 0 && (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--rr-slate-dark)" strokeWidth="1.5">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          )}
          {isLast || !item.href ? (
            <span style={{ color: isLast ? 'var(--rr-navy-800)' : 'var(--rr-slate-dark)', fontWeight: isLast ? 600 : 400 }}>
              {item.label}
            </span>
          ) : (
            <a href={item.href} style={{ color: 'var(--rr-slate-dark)', textDecoration: 'none' }}
              onMouseEnter={e => e.target.style.color = 'hsl(var(--primary))'}
              onMouseLeave={e => e.target.style.color = 'var(--rr-slate-dark)'}
            >
              {item.label}
            </a>
          )}
        </React.Fragment>
      );
    })}
  </nav>
);

window.Breadcrumb = Breadcrumb;
