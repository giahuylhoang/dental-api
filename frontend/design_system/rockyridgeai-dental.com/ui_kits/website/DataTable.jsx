// DataTable — standard table with optional row links and empty state
const DataTable = ({ columns, rows, onRowHref, empty }) => {
  if (!rows || rows.length === 0) {
    return empty || (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--rr-slate-dark)', fontFamily: 'var(--font-ui)', fontSize: '.88rem' }}>
        No records found.
      </div>
    );
  }

  const alignStyle = (align) => ({ textAlign: align || 'left' });

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-ui)', fontSize: '.88rem' }}>
      <thead>
        <tr>
          {columns.map(col => (
            <th key={col.key} style={{
              ...alignStyle(col.align),
              padding: '12px 14px',
              color: 'var(--rr-slate-dark)',
              fontSize: '.68rem',
              letterSpacing: '.08em',
              textTransform: 'uppercase',
              borderBottom: '1px solid var(--rr-parchment)',
              fontWeight: 600,
              width: col.width || undefined,
            }}>
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => {
          const href = onRowHref ? onRowHref(row) : null;
          const cells = columns.map(col => (
            <td key={col.key} style={{
              ...alignStyle(col.align),
              padding: '14px',
              borderBottom: i < rows.length - 1 ? '1px solid var(--rr-parchment)' : 'none',
              verticalAlign: 'middle',
              fontFamily: col.mono ? 'var(--font-mono)' : undefined,
              fontSize: col.mono ? '.76rem' : undefined,
            }}>
              {col.render ? col.render(row) : row[col.key]}
            </td>
          ));

          if (href) {
            return (
              <tr key={i} style={{ cursor: 'pointer' }}
                onClick={() => { window.location.href = href; }}
                onMouseEnter={e => { Array.from(e.currentTarget.cells).forEach(c => c.style.background = 'rgba(58,127,189,0.03)'); }}
                onMouseLeave={e => { Array.from(e.currentTarget.cells).forEach(c => c.style.background = ''); }}
              >
                {cells}
              </tr>
            );
          }
          return (
            <tr key={i}
              onMouseEnter={e => { Array.from(e.currentTarget.cells).forEach(c => c.style.background = 'rgba(58,127,189,0.03)'); }}
              onMouseLeave={e => { Array.from(e.currentTarget.cells).forEach(c => c.style.background = ''); }}
            >
              {cells}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
};

window.DataTable = DataTable;
