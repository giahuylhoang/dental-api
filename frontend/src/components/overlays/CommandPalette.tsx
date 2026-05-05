'use client';

import React from 'react';
import { Search, Plus } from 'lucide-react';
import { PATIENTS } from '@/lib/data';

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onNewAppt?: () => void;
}

export function CommandPalette({ open, onClose, onNewAppt }: CommandPaletteProps) {
  const [q, setQ] = React.useState('');

  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    if (open) document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  const pts = PATIENTS.filter(p => !q || (p.first + ' ' + p.last).toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="cmd-overlay" onClick={onClose}>
      <div className="cmd-palette" onClick={e => e.stopPropagation()}>
        <div className="cmd-input-wrap">
          <Search size={18} strokeWidth={1.5} />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search patients, invoices, appointments..." autoFocus />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '.68rem', color: 'var(--rr-slate-dark)', padding: '2px 6px', background: 'var(--rr-off-white)', border: '1px solid var(--rr-parchment)', borderRadius: 3 }}>⌘K</span>
        </div>
        <div className="cmd-group">
          <div className="cmd-heading">Patients</div>
          {pts.slice(0, 4).map(p => (
            <div key={p.id} className="cmd-item" onClick={onClose}>
              <span className="cmd-ava">{(p.first[0] + p.last[0]).toUpperCase()}</span>
              <div className="cmd-name">{p.first} {p.last}</div>
              <span className="cmd-sub">{p.id}</span>
            </div>
          ))}
        </div>
        <div className="cmd-group">
          <div className="cmd-heading">Quick actions</div>
          <div className="cmd-item" onClick={() => { onClose(); onNewAppt?.(); }}>
            <Plus size={16} strokeWidth={1.5} className="cmd-ico" />
            <div className="cmd-name">New appointment</div>
            <span className="cmd-sub">⌘⇧A</span>
          </div>
        </div>
        <div className="cmd-footer"><span>↑↓ navigate</span><span>↵ open</span><span>esc close</span></div>
      </div>
    </div>
  );
}
