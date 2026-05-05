'use client';

import React from 'react';
import Link from 'next/link';
import { PATIENTS as PATIENTS_MOCK, type Patient } from '@/lib/data';
import { StatusPill } from '@/components/domain/StatusPill';
import { Drawer } from '@/components/overlays/Drawer';
import { useToast } from '@/components/overlays/ToastContext';
import { api, ApiError } from '@/lib/api';

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === '1';

export default function PatientsPage() {
  const { addToast } = useToast();
  const [search, setSearch] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [newFirst, setNewFirst] = React.useState('');
  const [newLast, setNewLast] = React.useState('');
  const [newDob, setNewDob] = React.useState('');
  const [newPhone, setNewPhone] = React.useState('');
  const [newInsurance, setNewInsurance] = React.useState('');

  // Patients state — seeded from the mock so the UI renders during initial load,
  // then replaced by the live list when the API returns.
  const [patients, setPatients] = React.useState<Patient[]>(PATIENTS_MOCK);

  React.useEffect(() => {
    if (USE_MOCKS) return;
    api.patients.list()
      .then(rows => {
        setPatients(rows.map(r => ({
          id: r.id,
          first: r.first_name ?? '',
          last: r.last_name ?? '',
          dob: '',  // not returned by /api/patients list view
          insurance: '',
          last_visit: '',
          status: 'active',
        })));
      })
      .catch((e) => {
        if (e instanceof ApiError) console.warn('Patients load failed:', e.message);
      });
  }, []);

  const filtered = patients.filter(p => {
    if (statusFilter && p.status !== statusFilter) return false;
    if (search && !(p.first + ' ' + p.last + ' ' + p.id).toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const filters = ['active', 'recall', 'plan', 'inactive'];

  const handleSavePatient = async () => {
    if (USE_MOCKS) {
      const id = 'P-' + String(Math.floor(10000 + Math.random() * 90000));
      setPatients(prev => [...prev, { id, first: newFirst, last: newLast, dob: newDob, insurance: newInsurance, last_visit: 'New', status: 'active' }]);
      setDrawerOpen(false);
      addToast('Patient added (mock).', newFirst + ' ' + newLast);
      setNewFirst(''); setNewLast(''); setNewDob(''); setNewPhone(''); setNewInsurance('');
      return;
    }
    try {
      const created = await api.patients.create({
        first_name: newFirst,
        last_name: newLast,
      });
      setPatients(prev => [...prev, {
        id: created.id,
        first: created.first_name ?? newFirst,
        last: created.last_name ?? newLast,
        dob: newDob,
        insurance: newInsurance,
        last_visit: 'New',
        status: 'active',
      }]);
      setDrawerOpen(false);
      addToast('Patient added.', `${newFirst} ${newLast}`);
      setNewFirst(''); setNewLast(''); setNewDob(''); setNewPhone(''); setNewInsurance('');
    } catch (e) {
      addToast('Save failed: ' + (e instanceof ApiError ? e.message : 'network error'));
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Patients</h1>
          <div className="page-sub">{filtered.length} patients · {patients.filter(p => p.status === 'active').length} active</div>
        </div>
        <button className="btn btn-primary btn-md" onClick={() => setDrawerOpen(true)}>+ New patient</button>
      </div>

      <div className="panel" style={{ padding: '14px 18px' }}>
        <div className="toolbar">
          <div style={{ position: 'relative', flex: 1, minWidth: 240 }}>
            <svg style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: '#8A9BB0' }} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" placeholder="Search patients..." value={search} onChange={e => setSearch(e.target.value)}
              style={{ flex: 1, minWidth: 240, height: 38, padding: '0 12px 0 36px', borderRadius: 4, border: '1px solid #EDE9E0', background: '#FAF9F6', fontFamily: "'Inter', sans-serif", fontSize: '.88rem', color: '#1C2333', width: '100%' }}
            />
          </div>
          {filters.map(f => (
            <button key={f} className={'filter-pill' + (statusFilter === f ? ' active' : '')}
              onClick={() => setStatusFilter(statusFilter === f ? null : f)}
            >{f.charAt(0).toUpperCase() + f.slice(1)}</button>
          ))}
        </div>
      </div>

      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="list">
          <thead><tr><th>Patient</th><th>ID</th><th>Date of Birth</th><th>Insurance</th><th>Last Visit</th><th>Status</th></tr></thead>
          <tbody>
            {filtered.map(p => (
              <tr key={p.id} style={{ cursor: 'pointer' }} onClick={() => window.location.href = '/patients/' + p.id}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div className="avatar-sm" style={{ background: '#3A7FBD' }}>{(p.first[0] + p.last[0]).toUpperCase()}</div>
                    <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, color: '#1C2333' }}>{p.first} {p.last}</span>
                  </div>
                </td>
                <td className="id-cell">{p.id}</td>
                <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.82rem', color: '#4A5568' }}>{p.dob}</td>
                <td style={{ color: '#4A5568' }}>{p.insurance}</td>
                <td style={{ color: '#4A5568' }}>{p.last_visit}</td>
                <td><StatusPill status={p.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* New Patient Drawer */}
      {drawerOpen && (
        <Drawer open={true} onClose={() => setDrawerOpen(false)} meta="New patient" title="Add a new patient" sub="Fill in patient details below."
          footer={
            <>
              <button className="btn btn-ghost btn-md" onClick={() => setDrawerOpen(false)}>Cancel</button>
              <button className="btn btn-primary btn-md" disabled={!newFirst || !newLast} onClick={handleSavePatient}>Save patient</button>
            </>
          }
        >
          <div className="field-row">
            <div className="field"><label className="lbl">First name *</label><input className="d-input" value={newFirst} onChange={e => setNewFirst(e.target.value)} /></div>
            <div className="field"><label className="lbl">Last name *</label><input className="d-input" value={newLast} onChange={e => setNewLast(e.target.value)} /></div>
          </div>
          <div className="field"><label className="lbl">Date of birth</label><input type="date" className="d-input" value={newDob} onChange={e => setNewDob(e.target.value)} /></div>
          <div className="field-row">
            <div className="field"><label className="lbl">Phone</label><input className="d-input" value={newPhone} onChange={e => setNewPhone(e.target.value)} /></div>
            <div className="field"><label className="lbl">Insurance</label><input className="d-input" value={newInsurance} onChange={e => setNewInsurance(e.target.value)} /></div>
          </div>
        </Drawer>
      )}
    </>
  );
}
