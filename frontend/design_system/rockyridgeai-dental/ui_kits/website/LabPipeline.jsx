// LabPipeline.jsx — Lab queue Kanban (status columns: Sent · In progress · Returned · Seated)

const LAB_COLUMNS = [
  { id: 'sent',     label: 'Sent · waiting on lab',     count: 3 },
  { id: 'progress', label: 'In progress',               count: 2 },
  { id: 'returned', label: 'Returned · ready to seat',  count: 4 },
];

const LAB_CASES = [
  { id: 'LC-2026-0481', patient: 'Alice Stevens',  vendor: 'Pinnacle Dental Lab',   item: 'Crown · #36',           eta: '2026-05-12', col: 'sent'     },
  { id: 'LC-2026-0476', patient: 'Sofía Castillo', vendor: 'Crown City Lab',        item: 'Implant · #11',         eta: '2026-05-18', col: 'sent'     },
  { id: 'LC-2026-0474', patient: 'Marcus Doan',    vendor: 'Mountain Lab Services', item: 'Reline · upper denture',eta: '2026-05-08', col: 'progress' },
  { id: 'LC-2026-0469', patient: 'Priya Khanna',   vendor: 'Pinnacle Dental Lab',   item: 'Crown · #36',           eta: '2026-05-04', col: 'returned' },
  { id: 'LC-2026-0467', patient: 'Eli Brouwer',    vendor: 'Apex Ortho Lab',        item: 'Retainer',              eta: '2026-05-04', col: 'returned' },
];

const LabPipeline = ({ onCaseClick }) => (
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
    {LAB_COLUMNS.map(col => {
      const cards = LAB_CASES.filter(c => c.col === col.id);
      return (
        <div key={col.id} style={{ background: '#FAF9F6', border: '1px solid #EDE9E0', borderRadius: 6, padding: 12, display: 'flex', flexDirection: 'column', gap: 8, minHeight: 240 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 6px 8px' }}>
            <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: '#4A5568' }}>{col.label}</span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#3A7FBD', fontWeight: 600, padding: '1px 8px', background: '#D9EAF5', borderRadius: 999 }}>{cards.length}</span>
          </div>
          {cards.map(c => (
            <div key={c.id} style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 6, boxShadow: '0 1px 2px rgba(10,25,47,0.04)', cursor: 'pointer' }} onClick={() => onCaseClick && onCaseClick(c)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.85rem', color: '#1C2333' }}>{c.patient}</div>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.66rem', color: '#8A9BB0' }}>{c.id}</span>
              </div>
              <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.78rem', color: '#3D4D61' }}>{c.item}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.7rem', color: '#4A5568' }}>{c.vendor}</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#B45309' }}>ETA {c.eta}</span>
              </div>
            </div>
          ))}
        </div>
      );
    })}
  </div>
);

Object.assign(window, { LabPipeline, LAB_CASES, LAB_COLUMNS });
