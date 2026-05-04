// CalendarGrid — schedule day grid with absolute-positioned event blocks
const CalendarGrid = ({ slotMinutes, dayStartHour, dayEndHour, columns, events, nowMinutes }) => {
  const mins = slotMinutes || 30;
  const startH = dayStartHour != null ? dayStartHour : 8;
  const endH = dayEndHour != null ? dayEndHour : 18;
  const totalMins = (endH - startH) * 60;
  const slotCount = totalMins / mins;
  const ROW_H = 36;

  const slots = [];
  for (let i = 0; i <= slotCount; i++) {
    const m = startH * 60 + i * mins;
    const h = Math.floor(m / 60);
    const mm = m % 60;
    slots.push(`${String(h).padStart(2,'0')}:${String(mm).padStart(2,'0')}`);
  }

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: `56px repeat(${columns.length}, 1fr)`,
    gap: 1, background: '#EDE9E0', border: '1px solid #EDE9E0', borderRadius: 4, overflow: 'hidden',
  };

  const toPercent = (timeStr) => {
    const [h, m] = timeStr.split(':').map(Number);
    return ((h * 60 + m - startH * 60) / totalMins) * 100;
  };

  return (
    <div>
      <div style={gridStyle}>
        {/* Header row */}
        <div style={{ background: 'var(--rr-warm-white)', padding: '10px 12px' }}/>
        {columns.map(col => (
          <div key={col.key} style={{
            background: 'var(--rr-warm-white)', padding: '10px 12px',
            fontFamily: 'var(--font-ui)', fontSize: '.72rem', fontWeight: 600,
            letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--rr-slate-dark)',
          }}>
            {col.label}
          </div>
        ))}

        {/* Time rows */}
        {slots.slice(0, -1).map((slot, si) => (
          <React.Fragment key={si}>
            <div style={{
              background: 'var(--rr-warm-white)', padding: '4px 10px',
              fontFamily: 'var(--font-mono)', fontSize: '.7rem', color: 'var(--rr-slate-dark)',
              display: 'flex', alignItems: 'flex-start', minHeight: ROW_H,
            }}>
              {slot}
            </div>
            {columns.map(col => (
              <div key={col.key} style={{ background: '#fff', minHeight: ROW_H, position: 'relative' }}/>
            ))}
          </React.Fragment>
        ))}
      </div>

      {/* Events overlay */}
      <div style={{ position: 'relative', marginTop: -(slotCount * (ROW_H + 1) + ROW_H + 1), pointerEvents: 'none' }}>
        <div style={{ display: 'grid', gridTemplateColumns: `56px repeat(${columns.length}, 1fr)`, gap: 1 }}>
          <div style={{ height: ROW_H + 1 }}/>
          {columns.map(col => {
            const colEvents = events.filter(e => e.columnKey === col.key);
            const totalH = slotCount * (ROW_H + 1);
            return (
              <div key={col.key} style={{ position: 'relative', height: totalH + ROW_H + 1, pointerEvents: 'auto' }}>
                <div style={{ position: 'absolute', top: ROW_H + 1, left: 0, right: 0, bottom: 0 }}>
                  {colEvents.map((ev, ei) => {
                    const topPct = toPercent(ev.start);
                    const btmPct = toPercent(ev.end);
                    return (
                      <div key={ei} style={{
                        position: 'absolute',
                        top: `${topPct}%`, height: `${btmPct - topPct}%`,
                        left: 4, right: 4, borderRadius: 4,
                        background: ev.color || 'var(--rr-mist)',
                        padding: '6px 8px', boxShadow: '0 1px 2px rgba(10,25,47,0.08)',
                        cursor: 'pointer', overflow: 'hidden',
                      }}>
                        {ev.render ? ev.render(ev) : null}
                      </div>
                    );
                  })}
                  {nowMinutes != null && (() => {
                    const pct = ((nowMinutes - startH * 60) / totalMins) * 100;
                    if (pct < 0 || pct > 100) return null;
                    return (
                      <div style={{
                        position: 'absolute', left: 0, right: 0, top: `${pct}%`,
                        height: 2, background: '#9B2335', zIndex: 5,
                      }}>
                        <div style={{ position: 'absolute', left: -5, top: -3, width: 8, height: 8, borderRadius: '999px', background: '#9B2335' }}/>
                      </div>
                    );
                  })()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

window.CalendarGrid = CalendarGrid;
