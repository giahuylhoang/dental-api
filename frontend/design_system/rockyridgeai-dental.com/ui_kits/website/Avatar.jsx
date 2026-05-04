// Avatar — 3-letter monogram circle with deterministic color
const Avatar = ({ name, size, seed, href }) => {
  const sz = size || 36;
  const initials = (name || '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 3)
    .map(w => w[0].toUpperCase())
    .join('');

  const COLORS = ['#3A7FBD','#2A7D4F','#B45309','#2E6494','#0A192F','#9B2335','#4A5568'];
  const key = seed || name || '';
  let hash = 0;
  for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) & 0xffffffff;
  const bg = COLORS[Math.abs(hash) % COLORS.length];

  const circle = (
    <div style={{
      width: sz, height: sz, borderRadius: '999px', background: bg, color: '#fff',
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'var(--font-ui)', fontWeight: 600,
      fontSize: sz * 0.32 + 'px',
      flexShrink: 0,
    }}>
      {initials}
    </div>
  );

  if (href) {
    return <a href={href} style={{ textDecoration: 'none' }}>{circle}</a>;
  }
  return circle;
};

window.Avatar = Avatar;
