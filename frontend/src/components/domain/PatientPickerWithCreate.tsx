'use client';

import React from 'react';
import { useToast } from '@/components/overlays/ToastContext';
import { api, type PatientDTO } from '@/lib/api';

interface PatientPickerWithCreateProps {
  patients: PatientDTO[];
  value: PatientDTO | null;
  onChange: (p: PatientDTO | null) => void;
  onCreated: (p: PatientDTO) => void;
  disabled?: boolean;
}

function fullName(p: PatientDTO): string {
  return `${p.first_name ?? ''} ${p.last_name ?? ''}`.trim() || p.id;
}

function initials(p: PatientDTO): string {
  const f = (p.first_name ?? '').trim();
  const l = (p.last_name ?? '').trim();
  return ((f[0] ?? '') + (l[0] ?? '')).toUpperCase() || '?';
}

export function PatientPickerWithCreate({
  patients,
  value,
  onChange,
  onCreated,
  disabled,
}: PatientPickerWithCreateProps) {
  const { addToast } = useToast();
  const [mode, setMode] = React.useState<'search' | 'create'>('search');
  const [query, setQuery] = React.useState('');
  const [focus, setFocus] = React.useState(false);
  const [newFirst, setNewFirst] = React.useState('');
  const [newLast, setNewLast] = React.useState('');
  const [newPhone, setNewPhone] = React.useState('');
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (value && !query) setQuery(fullName(value));
  }, [value, query]);

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return patients.slice(0, 8);
    return patients
      .filter(p => {
        const name = fullName(p).toLowerCase();
        return name.includes(q) || p.id.toLowerCase().includes(q);
      })
      .slice(0, 8);
  }, [patients, query]);

  const pick = (p: PatientDTO) => {
    onChange(p);
    setQuery(fullName(p));
    setFocus(false);
  };

  const startCreate = () => {
    setNewFirst('');
    setNewLast('');
    setNewPhone('');
    setMode('create');
  };

  const cancelCreate = () => {
    setMode('search');
  };

  const submitCreate = async () => {
    if (!newFirst.trim() || !newLast.trim()) {
      addToast('First and last name are required.');
      return;
    }
    setSaving(true);
    try {
      const body: Partial<PatientDTO> = {
        first_name: newFirst.trim(),
        last_name: newLast.trim(),
      };
      if (newPhone.trim()) body.phone = newPhone.trim();
      const created = await api.patients.create(body);
      onCreated(created);
      onChange(created);
      setQuery(fullName(created));
      addToast('Patient added.', fullName(created));
      setMode('search');
    } catch {
      addToast('Failed to add patient.');
    } finally {
      setSaving(false);
    }
  };

  if (mode === 'create') {
    return (
      <div className="field">
        <div className="field-label-row">
          <label className="lbl">New patient</label>
          <a className="field-link" onClick={cancelCreate}>← Back to search</a>
        </div>
        <div className="field-row">
          <div className="field">
            <label className="lbl">First name *</label>
            <input
              className="d-input"
              value={newFirst}
              onChange={e => setNewFirst(e.target.value)}
              disabled={saving}
              autoFocus
            />
          </div>
          <div className="field">
            <label className="lbl">Last name *</label>
            <input
              className="d-input"
              value={newLast}
              onChange={e => setNewLast(e.target.value)}
              disabled={saving}
            />
          </div>
        </div>
        <div className="field">
          <label className="lbl">Phone (optional)</label>
          <input
            className="d-input"
            value={newPhone}
            onChange={e => setNewPhone(e.target.value)}
            disabled={saving}
            placeholder="5551234567"
          />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className="btn btn-ghost btn-md"
            onClick={cancelCreate}
            disabled={saving}
            type="button"
          >
            Cancel
          </button>
          <button
            className="btn btn-primary btn-md"
            onClick={submitCreate}
            disabled={saving || !newFirst.trim() || !newLast.trim()}
            type="button"
          >
            {saving ? 'Saving…' : 'Save patient'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="field">
      <div className="field-label-row">
        <label className="lbl">Patient</label>
        <a className="field-link" onClick={startCreate}>+ New patient</a>
      </div>
      <div className="search-select">
        <input
          className="d-input"
          placeholder={patients.length ? 'Search patients...' : 'No patients yet — click + New patient'}
          value={query}
          onChange={e => { setQuery(e.target.value); onChange(null); }}
          onFocus={() => setFocus(true)}
          onBlur={() => setTimeout(() => setFocus(false), 150)}
          disabled={disabled}
        />
        {focus && filtered.length > 0 && (
          <div className="search-results">
            {filtered.map(p => (
              <div
                key={p.id}
                className={'search-opt' + (value && value.id === p.id ? ' selected' : '')}
                onMouseDown={() => pick(p)}
              >
                <span className="search-ava">{initials(p)}</span>
                {fullName(p)}
                <span className="search-sub">{p.id.slice(0, 8)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
