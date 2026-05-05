'use client';

import React from 'react';
import { StatusPill } from '@/components/domain/StatusPill';
import { Drawer } from '@/components/overlays/Drawer';
import { CenterModal } from '@/components/overlays/CenterModal';
import { useToast } from '@/components/overlays/ToastContext';
import { ArrowLeft } from 'lucide-react';
import { api } from '@/lib/api';

interface TreatmentPlan {
  id: string;
  patient: string;
  condition: string;
  phases: number;
  completed: number;
  status: string;
  start: string;
  notes: string;
}

const SEED_PLANS: TreatmentPlan[] = [
  { id: 'TP-001', patient: 'Alice Stevens', condition: 'Crown #36', phases: 2, completed: 1, status: 'active', start: '2026-04-21', notes: 'Lab case LC-2026-0481. Material: zirconia.' },
  { id: 'TP-002', patient: 'Marcus Doan', condition: 'Upper full denture', phases: 4, completed: 0, status: 'pending', start: '2026-04-15', notes: 'Impressions pending. Patient needs pre-auth.' },
  { id: 'TP-003', patient: 'Priya Khanna', condition: 'Implant #11', phases: 3, completed: 3, status: 'completed', start: '2026-03-01', notes: 'All phases complete. Recall in 6 months.' },
  { id: 'TP-004', patient: 'Eli Brouwer', condition: 'Ortho retainers', phases: 1, completed: 1, status: 'completed', start: '2026-02-12', notes: 'Retainers delivered. Follow-up in 3 months.' },
];

const STATUSES = ['pending', 'active', 'completed', 'cancelled'];

export default function TreatmentPage() {
  const { addToast } = useToast();
  const [plans, setPlans] = React.useState<TreatmentPlan[]>(SEED_PLANS);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [detailId, setDetailId] = React.useState<string | null>(null);
  const [editing, setEditing] = React.useState(false);
  const [draft, setDraft] = React.useState<TreatmentPlan | null>(null);
  const [newPatient, setNewPatient] = React.useState('Alice Stevens');
  const [newCondition, setNewCondition] = React.useState('');
  const [newPhases, setNewPhases] = React.useState(3);
  const [submitting, setSubmitting] = React.useState(false);

  const detailPlan = detailId ? plans.find(p => p.id === detailId) ?? null : null;

  const handleCreatePlan = async () => {
    setSubmitting(true);
    try {
      const res = await api.v2.treatmentPlans.create({
        patient_id: newPatient.replace(/\s/g, '-').toLowerCase(),
        title: newCondition || 'Treatment Plan',
      }) as { id: string };
      const newPlan: TreatmentPlan = {
        id: res.id,
        patient: newPatient,
        condition: newCondition || 'Treatment Plan',
        phases: newPhases,
        completed: 0,
        status: 'pending',
        start: new Date().toISOString().slice(0, 10),
        notes: '',
      };
      setPlans(prev => [newPlan, ...prev]);
      addToast('Plan created.', res.id);
      setDrawerOpen(false);
      setNewCondition('');
    } catch { addToast('Failed to create plan.'); }
    finally { setSubmitting(false); }
  };

  const handlePresent = async (planId: string) => {
    try {
      await api.v2.treatmentPlans.present(planId);
      setPlans(prev => prev.map(p => p.id === planId ? { ...p, status: 'active' } : p));
      addToast('Plan presented.', planId);
    } catch { addToast('Failed to present plan.'); }
  };

  const handleAccept = async (planId: string) => {
    try {
      await api.v2.treatmentPlans.accept(planId);
      setPlans(prev => prev.map(p => p.id === planId ? { ...p, status: 'active' } : p));
      addToast('Plan accepted.', planId);
    } catch { addToast('Failed to accept plan.'); }
  };

  const handleDecline = async (planId: string) => {
    try {
      await api.v2.treatmentPlans.decline(planId);
      setPlans(prev => prev.map(p => p.id === planId ? { ...p, status: 'cancelled' } : p));
      addToast('Plan declined.', planId);
    } catch { addToast('Failed to decline plan.'); }
  };

  const handleComplete = async (planId: string) => {
    try {
      await api.v2.treatmentPlans.complete(planId);
      setPlans(prev => prev.map(p => p.id === planId ? { ...p, status: 'completed', completed: p.phases } : p));
      addToast('Plan completed.', planId);
    } catch { addToast('Failed to complete plan.'); }
  };

  const startEdit = () => {
    if (!detailPlan) return;
    setDraft({ ...detailPlan });
    setEditing(true);
  };

  const saveEdit = () => {
    if (!draft) return;
    setPlans(prev => prev.map(p => (p.id === draft.id ? draft : p)));
    addToast(`${draft.id} updated.`, draft.id);
    setEditing(false);
    setDraft(null);
  };

  const cancelEdit = () => {
    setEditing(false);
    setDraft(null);
  };

  const closeDetail = () => {
    setDetailId(null);
    setEditing(false);
    setDraft(null);
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Treatment Plans</h1>
          <div className="page-sub">{plans.length} plans · {plans.filter(t => t.status === 'active').length} active</div>
        </div>
        <button className="btn btn-primary btn-md" onClick={() => setDrawerOpen(true)}>+ New plan</button>
      </div>
      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="list">
          <thead><tr><th>Plan ID</th><th>Patient</th><th>Condition</th><th>Phases</th><th>Progress</th><th>Status</th></tr></thead>
          <tbody>
            {plans.map(tp => (
              <tr key={tp.id} style={{ cursor: 'pointer' }} onClick={() => { setDetailId(tp.id); setEditing(false); }}>
                <td className="id-cell">{tp.id}</td>
                <td style={{ fontWeight: 600 }}>{tp.patient}</td>
                <td>{tp.condition}</td>
                <td style={{ fontFamily: "'JetBrains Mono', monospace" }}>{tp.completed}/{tp.phases}</td>
                <td>
                  <div style={{ background: '#F5F2EC', borderRadius: 4, height: 8, width: 120, overflow: 'hidden' }}>
                    <div style={{ background: '#3A7FBD', height: '100%', width: `${(tp.completed / tp.phases) * 100}%`, borderRadius: 4 }} />
                  </div>
                </td>
                <td><StatusPill status={tp.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* New Plan Drawer */}
      {drawerOpen && (
        <Drawer open={true} onClose={() => setDrawerOpen(false)} meta="New plan" title="Create treatment plan" sub="Add condition and phases."
          footer={
            <>
              <button className="btn btn-ghost btn-md" onClick={() => setDrawerOpen(false)}>Cancel</button>
              <button className="btn btn-primary btn-md" disabled={submitting} onClick={handleCreatePlan}>{submitting ? 'Creating...' : 'Create plan'}</button>
            </>
          }
        >
          <div className="field"><label className="lbl">Patient</label>
            <select className="d-input" value={newPatient} onChange={e => setNewPatient(e.target.value)}>
              {['Alice Stevens', 'Marcus Doan', 'Priya Khanna', 'Eli Brouwer', 'Sofía Castillo', 'Daniel Okafor'].map(n => <option key={n}>{n}</option>)}
            </select>
          </div>
          <div className="field"><label className="lbl">Condition</label><input className="d-input" placeholder="e.g. Crown #36" value={newCondition} onChange={e => setNewCondition(e.target.value)} /></div>
          <div className="field-row">
            <div className="field"><label className="lbl">Phases</label><input className="d-input" type="number" value={newPhases} onChange={e => setNewPhases(Number(e.target.value) || 1)} /></div>
            <div className="field"><label className="lbl">Start date</label><input className="d-input" type="date" defaultValue="2026-05-04" /></div>
          </div>
          <div className="field"><label className="lbl">Notes</label><textarea className="d-textarea" placeholder="Clinical notes..." /></div>
        </Drawer>
      )}

      {/* Plan Detail Modal — overview + inline edit */}
      {detailPlan && (
        <CenterModal open={true} onClose={closeDetail} width="min(560px, 92vw)">
          <div className="center-modal-topbar">
            <button className="drawer-back" onClick={closeDetail}><ArrowLeft size={18} strokeWidth={1.5} /></button>
            <span className="back-label">{editing ? 'Editing plan' : 'Back to Treatment Plans'}</span>
          </div>
          <div className="center-modal-body">
            <div className="appt-ws-hero">
              <div className="appt-ws-ava">{detailPlan.patient.split(' ').map(s => s[0]).join('').toUpperCase()}</div>
              <div className="appt-ws-info">
                <div className="appt-ws-name">{detailPlan.patient}</div>
                <div className="appt-ws-detail">{(editing && draft ? draft.condition : detailPlan.condition)}</div>
                <div className="appt-ws-id">{detailPlan.id} · {(editing && draft ? draft.start : detailPlan.start)}</div>
              </div>
              <StatusPill status={(editing && draft ? draft.status : detailPlan.status)} />
            </div>

            {!editing && (
              <div>
                <div className="detail-row"><span className="detail-k">Plan ID</span><span className="detail-v">{detailPlan.id}</span></div>
                <div className="detail-row"><span className="detail-k">Condition</span><span className="detail-v">{detailPlan.condition}</span></div>
                <div className="detail-row"><span className="detail-k">Phases</span><span className="detail-v">{detailPlan.completed}/{detailPlan.phases} completed</span></div>
                <div className="detail-row"><span className="detail-k">Start</span><span className="detail-v">{detailPlan.start}</span></div>
                <div className="detail-row"><span className="detail-k">Notes</span><span className="detail-v">{detailPlan.notes}</span></div>
              </div>
            )}

            {editing && draft && (
              <div>
                <div className="field"><label className="lbl">Condition</label><input className="d-input" value={draft.condition} onChange={e => setDraft({ ...draft, condition: e.target.value })} /></div>
                <div className="field-row">
                  <div className="field"><label className="lbl">Phases</label><input className="d-input" type="number" min={1} value={draft.phases} onChange={e => setDraft({ ...draft, phases: Math.max(1, Number(e.target.value) || 1) })} /></div>
                  <div className="field"><label className="lbl">Completed</label><input className="d-input" type="number" min={0} max={draft.phases} value={draft.completed} onChange={e => setDraft({ ...draft, completed: Math.max(0, Math.min(draft.phases, Number(e.target.value) || 0)) })} /></div>
                </div>
                <div className="field-row">
                  <div className="field"><label className="lbl">Status</label>
                    <select className="d-input" value={draft.status} onChange={e => setDraft({ ...draft, status: e.target.value })}>
                      {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div className="field"><label className="lbl">Start date</label><input className="d-input" type="date" value={draft.start} onChange={e => setDraft({ ...draft, start: e.target.value })} /></div>
                </div>
                <div className="field"><label className="lbl">Notes</label><textarea className="d-textarea" value={draft.notes} onChange={e => setDraft({ ...draft, notes: e.target.value })} /></div>
              </div>
            )}

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {!editing && (
                <>
                  <button className="btn btn-primary btn-md" onClick={startEdit}>Edit plan</button>
                  {detailPlan.status === 'pending' && <button className="btn btn-ghost btn-md" onClick={() => handlePresent(detailPlan.id)}>Present</button>}
                  {detailPlan.status === 'pending' && <button className="btn btn-ghost btn-md" onClick={() => handleAccept(detailPlan.id)}>Accept</button>}
                  {detailPlan.status === 'pending' && <button className="btn btn-ghost btn-md" onClick={() => handleDecline(detailPlan.id)}>Decline</button>}
                  {detailPlan.status === 'active' && <button className="btn btn-ghost btn-md" onClick={() => handleComplete(detailPlan.id)}>Complete</button>}
                  <button className="btn btn-ghost btn-md" onClick={closeDetail}>Close</button>
                </>
              )}
              {editing && (
                <>
                  <button className="btn btn-primary btn-md" onClick={saveEdit}>Save changes</button>
                  <button className="btn btn-ghost btn-md" onClick={cancelEdit}>Cancel</button>
                </>
              )}
            </div>
          </div>
        </CenterModal>
      )}
    </>
  );
}
