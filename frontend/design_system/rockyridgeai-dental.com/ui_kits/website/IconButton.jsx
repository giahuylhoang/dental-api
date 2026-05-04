// IconButton — 32px square button with SVG child
const IconButton = ({ label, onClick, href, variant, children }) => {
  const isGhost = !variant || variant === 'ghost';
  const style = {
    width: 32, height: 32, borderRadius: 4, border: 'none',
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer', padding: 0, textDecoration: 'none',
    background: isGhost ? 'transparent' : 'hsl(var(--primary))',
    color: isGhost ? 'var(--rr-slate-dark)' : '#fff',
    transition: 'background 200ms',
  };

  const handleMouseEnter = (e) => {
    e.currentTarget.style.background = isGhost ? 'var(--rr-off-white)' : 'hsl(var(--primary) / 0.85)';
  };
  const handleMouseLeave = (e) => {
    e.currentTarget.style.background = isGhost ? 'transparent' : 'hsl(var(--primary))';
  };

  if (href) {
    return (
      <a href={href} aria-label={label} style={style} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
        {children}
      </a>
    );
  }
  return (
    <button onClick={onClick} aria-label={label} style={style} onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
      {children}
    </button>
  );
};

window.IconButton = IconButton;
