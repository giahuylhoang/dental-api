'use client';

import React from 'react';
import { Drawer } from '@/components/overlays/Drawer';
import { useToast } from '@/components/overlays/ToastContext';
import { api, type BusyBlockDTO, type ProviderDTO } from '@/lib/api';

interface BusyBlocksDrawerProps {
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
}

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

type Draft = {
  id?: number;
  provider_id: number | null;
  weekday: number;
  start_hour: number;
  start_minute: number;
  end_hour: number;
  end_minute: number;
  label: string;
};

const EMPTY_DRAFT: Draft = {
  provider_id: null,
  weekday: 0,
  start_hour: 12,
  start_minute: 0,
  end_hour: 13,
  end_minute: 0,
  label: '',
};

function pad2(n: number) { return n.toString().padStart(2, '0'); }
function fmtTime(h: number, m: number) { return `${pad2(h)}:${pad2(m)}`; }
function parseTime(s: string): { h: number; m: number } {
  const [h, m] = s.split(':').map(x => parseInt(x, 10));
  return { h: Number.isFinite(h) ? h : 0, m: Number.isFinite(m) ? m : 0 };
}

export function BusyBlocksDrawer({ open, onClose, onChanged }: BusyBlocksDrawerProps) {
  const { addToast } = useToast();
  const [providers, setProviders] = React.useState<ProviderDTO[]>([]);
  const [blocks, setBlocks] = React.useState<BusyBlockDTO[]>([]);
  const [editing, setEditing] = React.useState<Draft | null>(null);
  const [saving, setSaving] = React.useState(false);

  const refresh = React.useCallback(async () => {
    try {
      const rows = await api.v2.scheduling.busyBlocks.list();
      setBlocks(rows);
    } catch {
      addToast('Failed to load busy blocks.');
    }
  }, [addToast]);

  React.useEffect(() => {
    if (!open) return;
    api.providers.list().then(setProviders).catch(() => addToast('Failed to load providers.'));
    refresh();
  }, [open, refresh, addToast]);

  const providerName = React.useCallback((id: number) => {
    const p = providers.find(x => x.id === id);
    if (!p) return `Provider ${id}`;
    return [p.title, p.name].filter(Boolean).join(' ');
  }, [providers]);

  const startNew = () => {
    setEditing({ ...EMPTY_DRAFT, provider_id: providers[0]?.id ?? null });
  };

  const startEdit = (b: BusyBlockDTO) => {
    setEditing({
      id: b.id,
      provider_id: b.provider_id,
      weekday: b.weekday,
      start_hour: b.start_hour,
      start_minute: b.start_minute,
      end_hour: b.end_hour,
      end_minute: b.end_minute,
      label: b.label ?? '',
    });
  };

  const cancelEdit = () => setEditing(null);

  const save = async () => {
    if (!editing) return;
    if (editing.provider_id == null) { addToast('Pick a provider.'); return; }
    if ((editing.start_hour, editing.start_minute) >= (editing.end_hour, editing.end_minute)
        && !(editing.start_hour < editing.end_hour
             || (editing.start_hour === editing.end_hour && editing.start_minute < editing.end_minute))) {
      addToast('Start time must be before end time.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        provider_id: editing.provider_id,
        weekday: editing.weekday,
        start_hour: editing.start_hour,
        start_minute: editing.start_minute,
        end_hour: editing.end_hour,
        end_minute: editing.end_minute,
        label: editing.label.trim() || null,
      };
      if (editing.id != null) {
        await api.v2.scheduling.busyBlocks.update(editing.id, payload);
        addToast('Busy block updated.');
      } else {
        await api.v2.scheduling.busyBlocks.create(payload);
        addToast('Busy block added.');
      }
      setEditing(null);
      await refresh();
      onChanged();
    } catch {
      addToast('Failed to save busy block.');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: number) => {
    try {
      await api.v2.scheduling.busyBlocks.delete(id);
      addToast('Busy block removed.');
      await refresh();
      onChanged();
    } catch {
      addToast('Failed to delete busy block.');
    }
  };

  const grouped = React.useMemo(() => {
    const map = new Map<number, BusyBlockDTO[]>();
    for (const b of blocks) {
      const arr = map.get(b.provider_id) ?? [];
      arr.push(b);
      map.set(b.provider_id, arr);
    }
    return Array.from(map.entries()).map(([pid, list]) => ({
      provider_id: pid,
      list: list.sort((a, c) =>
        a.weekday - c.weekday
        || a.start_hour - c.start_hour
        || a.start_minute - c.start_minute),
    }));
  }, [blocks]);

  return (
    <Drawer
      open={open}
      onClose={() => { setEditing(null); onClose(); }}
      meta="Manage"
      title="Busy blocks"
      sub="Recurring weekly windows when a provider is unavailable."
      footer={
        editing ? (
          <>
            <button className="btn btn-ghost btn-md" onClick={cancelEdit} disabled={saving}>Cancel</button>
            <button className="btn btn-primary btn-md" onClick={save} disabled={saving}>{editing.id != null ? 'Save changes' : 'Add busy block'}</button>
          </>
        ) : (
          <>
            <button className="btn btn-ghost btn-md" onClick={onClose}>Close</button>
            <button className="btn btn-primary btn-md" onClick={startNew} disabled={providers.length === 0}>+ New busy block</button>
          </>
        )
      }
    >
      {!editing && grouped.length === 0 && (
        <div style={{ color: 'var(--rr-slate-dark)', fontFamily: 'var(--font-ui)', fontSize: '.85rem', padding: '12px 0' }}>
          No busy blocks for this clinic. Add one to mark a recurring window when a provider is unavailable.
        </div>
      )}

      {!editing && grouped.map(({ provider_id, list }) => (
        <div key={provider_id} style={{ marginBottom: 16 }}>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: '.72rem', fontWeight: 600, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--rr-slate-dark)', marginBottom: 8 }}>
            {providerName(provider_id)}
          </div>
          <table className="list">
            <thead>
              <tr><th>Day</th><th>Window</th><th>Label</th><th></th></tr>
            </thead>
            <tbody>
              {list.map(b => (
                <tr key={b.id}>
                  <td>{WEEKDAYS[b.weekday] ?? b.weekday}</td>
                  <td className="id-cell">{fmtTime(b.start_hour, b.start_minute)}–{fmtTime(b.end_hour, b.end_minute)}</td>
                  <td>{b.label ?? <span style={{ color: 'var(--rr-slate)' }}>—</span>}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => startEdit(b)}>Edit</button>{' '}
                    <button className="btn btn-ghost btn-sm" onClick={() => remove(b.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {editing && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="field">
            <label className="lbl">Provider</label>
            <select
              className="d-input"
              value={editing.provider_id ?? ''}
              onChange={e => setEditing({ ...editing, provider_id: e.target.value ? Number(e.target.value) : null })}
            >
              {providers.length === 0 && <option value="">(no providers loaded)</option>}
              {providers.map(p => (
                <option key={p.id} value={p.id}>{[p.title, p.name].filter(Boolean).join(' ') || `Provider ${p.id}`}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label className="lbl">Weekday</label>
            <select
              className="d-input"
              value={editing.weekday}
              onChange={e => setEditing({ ...editing, weekday: parseInt(e.target.value, 10) })}
            >
              {WEEKDAYS.map((name, idx) => (
                <option key={idx} value={idx}>{['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][idx]}</option>
              ))}
            </select>
          </div>
          <div className="field-row">
            <div className="field">
              <label className="lbl">Start</label>
              <input
                type="time"
                className="d-input"
                value={fmtTime(editing.start_hour, editing.start_minute)}
                onChange={e => { const { h, m } = parseTime(e.target.value); setEditing({ ...editing, start_hour: h, start_minute: m }); }}
              />
            </div>
            <div className="field">
              <label className="lbl">End</label>
              <input
                type="time"
                className="d-input"
                value={fmtTime(editing.end_hour, editing.end_minute)}
                onChange={e => { const { h, m } = parseTime(e.target.value); setEditing({ ...editing, end_hour: h, end_minute: m }); }}
              />
            </div>
          </div>
          <div className="field">
            <label className="lbl">Label (optional)</label>
            <input
              type="text"
              className="d-input"
              maxLength={64}
              value={editing.label}
              placeholder="e.g. Lunch, Hospital rounds"
              onChange={e => setEditing({ ...editing, label: e.target.value })}
            />
          </div>
        </div>
      )}
    </Drawer>
  );
}
