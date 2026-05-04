// KanbanBoard — generalized Kanban column layout
const KanbanBoard = ({ columns, cards, getColumn, renderCard, onCardHref }) => (
  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${columns.length}, 1fr)`, gap: 14 }}>
    {columns.map(col => {
      const colCards = cards.filter(c => getColumn(c) === col.key);
      return (
        <div key={col.key} style={{
          background: 'var(--rr-warm-white)', border: '1px solid var(--rr-parchment)',
          borderRadius: 6, padding: 12, display: 'flex', flexDirection: 'column', gap: 10, minHeight: 480,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 4px 6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-ui)', fontSize: '.7rem', fontWeight: 700, letterSpacing: '.12em', textTransform: 'uppercase', color: 'var(--rr-navy-800)' }}>
              {col.dot && <span style={{ width: 9, height: 9, borderRadius: '999px', background: col.dot, display: 'inline-block' }}/>}
              {col.label}
            </div>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '.7rem', color: 'var(--rr-steel-700)', padding: '2px 8px', background: 'var(--rr-mist)', borderRadius: '999px', fontWeight: 600 }}>
              {colCards.length}
            </span>
          </div>
          {colCards.map((card, i) => {
            const href = onCardHref ? onCardHref(card) : null;
            const content = renderCard(card);
            if (href) {
              return <a key={i} href={href} style={{ textDecoration: 'none', color: 'inherit' }}>{content}</a>;
            }
            return <React.Fragment key={i}>{content}</React.Fragment>;
          })}
        </div>
      );
    })}
  </div>
);

window.KanbanBoard = KanbanBoard;
