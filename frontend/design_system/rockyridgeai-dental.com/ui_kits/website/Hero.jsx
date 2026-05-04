// Hero.jsx — Rockyridge Dental AI marketing hero
// Mirrors rockyridgeai.com/Hero.jsx pattern: animated node graph + cycling display word.

const CYCLE_WORDS = ['Schedules.', 'Charts.', 'Plans.', 'Practices.'];

const NODES = [
  { id: 'patient',  label: 'Patient',     x: 0.72, y: 0.14, pillar: 1 },
  { id: 'chart',    label: 'Chart',       x: 0.55, y: 0.28, pillar: 1 },
  { id: 'sched',    label: 'Schedule',    x: 0.85, y: 0.36, pillar: 1 },
  { id: 'plan',     label: 'Plan',        x: 0.65, y: 0.50, pillar: 2 },
  { id: 'lab',      label: 'Lab',         x: 0.82, y: 0.60, pillar: 2 },
  { id: 'invoice',  label: 'Invoice',     x: 0.52, y: 0.65, pillar: 2 },
  { id: 'recall',   label: 'Recall',      x: 0.70, y: 0.78, pillar: 3 },
  { id: 'sms',      label: 'SMS · Email', x: 0.88, y: 0.82, pillar: 3 },
  { id: 'insurance',label: 'Insurance',   x: 0.58, y: 0.42, pillar: 2 },
];

const EDGES = [
  ['patient','chart'], ['patient','sched'], ['chart','plan'], ['chart','insurance'],
  ['sched','plan'], ['insurance','plan'], ['insurance','invoice'], ['plan','lab'],
  ['plan','recall'], ['invoice','recall'], ['lab','sms'], ['recall','sms'],
];

const PILLAR_COLOR = { 1: '#3A7FBD', 2: '#4A90D4', 3: '#6BAED6' };

const NodeGraph = ({ dark = true }) => {
  const canvasRef = React.useRef(null);
  const stateRef = React.useRef({ t: 0, particles: [], nodes: [] });

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let raf;

    const init = () => {
      const W = canvas.width  = canvas.offsetWidth;
      const H = canvas.height = canvas.offsetHeight;
      stateRef.current.nodes = NODES.map(n => ({ ...n, px: n.x * W, py: n.y * H, ox: n.x * W, oy: n.y * H, phase: Math.random() * Math.PI * 2, r: n.id === 'plan' ? 7 : 5 }));
      const particles = [];
      EDGES.forEach(([a, b]) => {
        for (let i = 0; i < 2; i++) particles.push({ from: a, to: b, t: Math.random(), speed: 0.003 + Math.random() * 0.003, reverse: Math.random() > 0.5 });
      });
      stateRef.current.particles = particles;
    };
    const draw = () => {
      const W = canvas.width, H = canvas.height;
      const ctx = canvas.getContext('2d');
      const s = stateRef.current; s.t += 0.008;
      ctx.clearRect(0, 0, W, H);
      const byId = {};
      s.nodes.forEach(n => { n.px = n.ox + Math.sin(s.t * 0.7 + n.phase) * 6; n.py = n.oy + Math.cos(s.t * 0.5 + n.phase) * 5; byId[n.id] = n; });
      EDGES.forEach(([a, b]) => {
        const na = byId[a], nb = byId[b]; if (!na || !nb) return;
        ctx.beginPath(); ctx.moveTo(na.px, na.py); ctx.lineTo(nb.px, nb.py);
        ctx.strokeStyle = dark ? 'rgba(58,127,189,0.18)' : 'rgba(10,25,47,0.12)';
        ctx.lineWidth = 1; ctx.stroke();
      });
      s.particles.forEach(p => {
        p.t += p.speed * (p.reverse ? -1 : 1);
        if (p.t > 1) p.t = 0; if (p.t < 0) p.t = 1;
        const na = byId[p.from], nb = byId[p.to]; if (!na || !nb) return;
        const x = na.px + (nb.px - na.px) * p.t, y = na.py + (nb.py - na.py) * p.t;
        ctx.beginPath(); ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = dark ? 'rgba(107,174,214,0.85)' : 'rgba(58,127,189,0.7)'; ctx.fill();
      });
      s.nodes.forEach(n => {
        const col = PILLAR_COLOR[n.pillar];
        if (n.id === 'plan') {
          const pulse = 0.4 + 0.3 * Math.sin(s.t * 2);
          ctx.beginPath(); ctx.arc(n.px, n.py, 18, 0, Math.PI * 2);
          ctx.strokeStyle = dark ? `rgba(58,127,189,${pulse})` : `rgba(58,127,189,${pulse * 0.6})`;
          ctx.lineWidth = 1; ctx.stroke();
        }
        ctx.beginPath(); ctx.arc(n.px, n.py, n.r, 0, Math.PI * 2);
        ctx.fillStyle = col; ctx.fill();
        ctx.beginPath(); ctx.arc(n.px, n.py, n.r * 0.45, 0, Math.PI * 2);
        ctx.fillStyle = dark ? 'rgba(10,25,47,0.5)' : 'rgba(255,255,255,0.6)'; ctx.fill();
        ctx.font = '500 10px Inter, sans-serif';
        ctx.fillStyle = dark ? 'rgba(250,249,246,0.55)' : 'rgba(10,25,47,0.5)';
        ctx.textAlign = 'center'; ctx.fillText(n.label, n.px, n.py + n.r + 13);
      });
      raf = requestAnimationFrame(draw);
    };
    init(); draw();
    const ro = new ResizeObserver(() => init()); ro.observe(canvas);
    return () => { cancelAnimationFrame(raf); ro.disconnect(); };
  }, [dark]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />;
};

const Hero = ({ onNav }) => {
  const [wordIdx, setWordIdx] = React.useState(0);
  const [visible, setVisible] = React.useState(true);

  React.useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => { setWordIdx(i => (i + 1) % CYCLE_WORDS.length); setVisible(true); }, 380);
    }, 2800);
    return () => clearInterval(id);
  }, []);

  return (
    <section style={{ background: '#0A192F', minHeight: '100vh', display: 'grid', gridTemplateColumns: '1fr 1fr', alignItems: 'center', padding: '100px 0 60px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ padding: '0 48px 0 calc(max(48px, (100% - 1200px) / 2 + 48px))', maxWidth: 660 }}>
        <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#3A7FBD', marginBottom: 24 }}>
          Rockyridge Dental AI · Systems Thinking for Practice Operations
        </div>
        <h1 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 900, fontSize: 'clamp(2.4rem,4.5vw,4rem)', lineHeight: 1.08, letterSpacing: '-0.03em', color: '#FAF9F6', margin: 0 }}>
          Architecting<br />Sovereign{' '}
          <span style={{
            display: 'inline-block', color: '#6BAED6',
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(10px)',
            transition: 'opacity 320ms cubic-bezier(0.16,1,0.3,1), transform 320ms cubic-bezier(0.16,1,0.3,1)',
            minWidth: '4ch',
          }}>{CYCLE_WORDS[wordIdx]}</span>
        </h1>
        <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '1.05rem', lineHeight: 1.8, color: 'rgba(250,249,246,0.6)', marginTop: 24, maxWidth: 480 }}>
          The dental practice OS for clinics that want their schedule, their charts, their lab cases, and their insurance reconciliation — all in one place, owned by the clinic.
        </p>
        <div style={{ display: 'flex', gap: 16, marginTop: 40, flexWrap: 'wrap', alignItems: 'center' }}>
          <button onClick={() => onNav?.('contact')} className="btn btn-white btn-lg">Schedule a demo</button>
          <button onClick={() => onNav?.('services')} className="btn btn-white btn-lg" style={{ opacity: 0.6 }}>See it work</button>
        </div>
        <div style={{ display: 'flex', gap: 40, marginTop: 60, paddingTop: 36, borderTop: '1px solid rgba(255,255,255,0.09)', flexWrap: 'wrap' }}>
          {[['Three Pillars','Schedule · Chart · Lab'], ['Sovereign','Your data, your servers'], ['Audit-logged','Always · forever']].map(([s, d]) => (
            <div key={s}>
              <div style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1rem', color: '#FAF9F6', letterSpacing: '-0.01em' }}>{s}</div>
              <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.75rem', color: 'rgba(250,249,246,0.4)', marginTop: 3, letterSpacing: '0.03em' }}>{d}</div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ height: '100vh', position: 'relative', opacity: 0.9 }}>
        {[['THE SCHEDULE', '14%'], ['THE CHART', '47%'], ['THE LAB', '76%']].map(([lbl, top]) => (
          <div key={lbl} style={{
            position: 'absolute', left: 8, top,
            fontFamily: "'Inter', sans-serif", fontWeight: 700, fontSize: '0.6rem',
            letterSpacing: '0.14em', textTransform: 'uppercase',
            color: 'rgba(58,127,189,0.35)', writingMode: 'vertical-rl',
            transform: 'rotate(180deg)', userSelect: 'none',
          }}>{lbl}</div>
        ))}
        {['33.3%', '66.6%'].map(top => (
          <div key={top} style={{ position: 'absolute', left: 32, right: 0, top, height: 1, background: 'rgba(58,127,189,0.07)' }} />
        ))}
        <NodeGraph dark={true} />
      </div>
    </section>
  );
};

Object.assign(window, { Hero, NodeGraph });
