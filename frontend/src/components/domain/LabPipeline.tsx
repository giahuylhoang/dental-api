'use client';

import { LabCase, LAB_CASES, LAB_COLUMNS } from '@/lib/data';

interface LabPipelineProps {
  onCaseClick?: (c: LabCase) => void;
  cases?: LabCase[];
}

export function LabPipeline({ onCaseClick, cases }: LabPipelineProps) {
  const source = cases ?? LAB_CASES;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
      {LAB_COLUMNS.map(col => {
        const cards = source.filter(c => c.col === col.id);
        return (
          <div key={col.id} style={{ background: '#FAF9F6', border: '1px solid #EDE9E0', borderRadius: 6, padding: 12, display: 'flex', flexDirection: 'column', gap: 8, minHeight: 240 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 6px 8px' }}>
              <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.7rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: '#4A5568' }}>{col.label}</span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#3A7FBD', fontWeight: 600, padding: '1px 8px', background: '#D9EAF5', borderRadius: 999 }}>{cards.length}</span>
            </div>
            {cards.map(c => (
              <div key={c.id} style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 6, boxShadow: '0 1px 2px rgba(10,25,47,0.04)', cursor: 'pointer' }}
                onClick={() => onCaseClick && onCaseClick(c)}
              >
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
}
