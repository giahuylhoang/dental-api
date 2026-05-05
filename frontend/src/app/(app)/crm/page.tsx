'use client';

import React, { useEffect, useState } from 'react';
import { useToast } from '@/components/overlays/ToastContext';
import { KpiTile } from '@/components/domain/KpiTile';
import { Drawer } from '@/components/overlays/Drawer';
import { StatusPill } from '@/components/domain/StatusPill';
import { Phone, Mail, MessageCircle, PenLine, Calendar } from 'lucide-react';
import { api } from '@/lib/api';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDroppable,
  useDraggable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';

type LeadStatus = 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'CONVERTED' | 'LOST';

interface Lead {
  id: string;
  first: string;
  last: string;
  email: string;
  phone: string;
  status: LeadStatus;
  source: string;
  owner: string;
  notes: string;
}

interface Activity {
  id: string;
  kind: string;
  body: string;
  occurred_at: string;
}

const COLUMNS: { id: LeadStatus; label: string; dot: string }[] = [
  { id: 'NEW', label: 'New', dot: '#8A9BB0' },
  { id: 'CONTACTED', label: 'Contacted', dot: '#3A7FBD' },
  { id: 'QUALIFIED', label: 'Qualified', dot: '#B45309' },
  { id: 'CONVERTED', label: 'Converted', dot: '#2A7D4F' },
  { id: 'LOST', label: 'Lost', dot: '#9B2335' },
];

const iconMap: Record<string, { cls: string; el: React.ReactNode }> = {
  call: { cls: 'ti-call', el: <Phone size={12} /> },
  email: { cls: 'ti-email', el: <Mail size={12} /> },
  sms: { cls: 'ti-sms', el: <MessageCircle size={12} /> },
  note: { cls: 'ti-note', el: <PenLine size={12} /> },
  meeting: { cls: 'ti-meeting', el: <Calendar size={12} /> },
};

function LeadCard({ lead, onClick, selected, dragging }: { lead: Lead; onClick: () => void; selected: boolean; dragging?: boolean }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({ id: lead.id });
  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      className={'lead-card' + (selected ? ' selected' : '') + (isDragging || dragging ? ' dragging' : '')}
      onClick={(e) => { if (isDragging) return; onClick(); e.stopPropagation(); }}
      data-testid={`lead-card-${lead.id}`}
    >
      <div className="lead-name">
        {lead.first} {lead.last}
        <span className="lead-source">{lead.source}</span>
      </div>
      <div className="lead-contact"><Phone size={11} /> {lead.phone}</div>
      <div className="lead-notes">{lead.notes}</div>
      <div className="lead-foot">
        <div className="lead-owner"><span className="avatar-mini">{lead.owner?.slice(0, 2) || '?'}</span> {lead.owner}</div>
      </div>
    </div>
  );
}

function Column({ col, leads, selectedId, onSelect, isOver }: { col: typeof COLUMNS[0]; leads: Lead[]; selectedId: string | null; onSelect: (l: Lead) => void; isOver: boolean }) {
  const { setNodeRef, isOver: dropping } = useDroppable({ id: col.id });
  return (
    <div ref={setNodeRef} className={'col' + (dropping || isOver ? ' col-drop' : '')} data-testid={`col-${col.id}`}>
      <div className="col-head">
        <div className="col-label"><span className="col-dot" style={{ background: col.dot }} />{col.label}</div>
        <span className="col-count">{leads.length}</span>
      </div>
      {leads.map(l => (
        <LeadCard key={l.id} lead={l} selected={selectedId === l.id} onClick={() => onSelect(l)} />
      ))}
    </div>
  );
}

export default function CRMPage() {
  const { addToast } = useToast();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [drawerTab, setDrawerTab] = useState(0);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);

  // New lead form
  const [newFirst, setNewFirst] = useState('');
  const [newLast, setNewLast] = useState('');
  const [newPhone, setNewPhone] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newSource, setNewSource] = useState('Google');
  const [newNotes, setNewNotes] = useState('');

  // Activity form
  const [activityKind, setActivityKind] = useState('note');
  const [activityBody, setActivityBody] = useState('');

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const fetchLeads = async () => {
    try {
      const data = await api.v2.crm.leads.list() as Array<{
        id: string; first_name: string; last_name: string; email: string; phone: string;
        status: string; source: string; owner_id: string; notes: string;
      }>;
      setLeads(data.map(l => ({
        id: l.id,
        first: l.first_name || '',
        last: l.last_name || '',
        email: l.email || '',
        phone: l.phone || '',
        status: (l.status || 'NEW') as LeadStatus,
        source: l.source || '',
        owner: l.owner_id || '',
        notes: l.notes || '',
      })));
    } catch (e) {
      console.error('Failed to load leads', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchActivities = async (leadId: string) => {
    try {
      const data = await api.v2.crm.leads.listActivities(leadId) as Activity[];
      setActivities(data);
    } catch { setActivities([]); }
  };

  useEffect(() => { fetchLeads(); }, []);

  useEffect(() => {
    if (selectedLead && drawerTab === 1) {
      fetchActivities(selectedLead.id);
    }
  }, [selectedLead, drawerTab]);

  const colLeads = (status: LeadStatus) => leads.filter(l => l.status === status);
  const activeLead = activeId ? leads.find(l => l.id === activeId) ?? null : null;

  const onDragStart = (e: DragStartEvent) => setActiveId(String(e.active.id));
  const onDragEnd = async (e: DragEndEvent) => {
    setActiveId(null);
    const overId = e.over?.id as LeadStatus | undefined;
    const leadId = String(e.active.id);
    if (!overId) return;
    const lead = leads.find(l => l.id === leadId);
    if (!lead || lead.status === overId) return;

    // Optimistic update
    setLeads(prev => prev.map(l => (l.id === leadId ? { ...l, status: overId } : l)));
    addToast(`${lead.first} ${lead.last} → ${COLUMNS.find(c => c.id === overId)?.label}`, lead.id);

    // API call
    try {
      await api.v2.crm.leads.update(leadId, { status: overId });
    } catch (e) {
      // Revert on failure
      setLeads(prev => prev.map(l => (l.id === leadId ? { ...l, status: lead.status } : l)));
      addToast('Failed to update status', '');
    }
  };

  const handleCreateLead = async () => {
    if (!newFirst.trim() || !newLast.trim()) {
      addToast('First and last name required', '');
      return;
    }
    try {
      await api.v2.crm.leads.create({
        first_name: newFirst,
        last_name: newLast,
        phone: newPhone,
        email: newEmail,
        source: newSource,
        notes: newNotes,
      });
      setDrawerOpen(false);
      setNewFirst(''); setNewLast(''); setNewPhone(''); setNewEmail(''); setNewNotes('');
      addToast('Lead created.', '');
      await fetchLeads();
    } catch (e) {
      addToast('Failed to create lead', '');
    }
  };

  const handleAddActivity = async () => {
    if (!selectedLead || !activityBody.trim()) return;
    try {
      await api.v2.crm.leads.addActivity(selectedLead.id, { kind: activityKind, body: activityBody });
      setActivityBody('');
      await fetchActivities(selectedLead.id);
      addToast('Activity added', '');
    } catch (e) {
      addToast('Failed to add activity', '');
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <>
      <style>{`
        .kanban { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; }
        .kanban .col { background: var(--rr-warm-white); border: 1px solid var(--rr-parchment); border-radius: 6px; padding: 12px; display: flex; flex-direction: column; gap: 10px; min-height: 480px; transition: background 160ms, border-color 160ms; }
        .kanban .col.col-drop { background: #EEF4FA; border-color: var(--rr-steel-500); }
        .col-head { display: flex; justify-content: space-between; align-items: center; padding: 4px 4px 6px; }
        .col-label { display: flex; align-items: center; gap: 8px; font-family: var(--font-ui); font-size: .7rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--rr-navy-800); }
        .col-dot { width: 9px; height: 9px; border-radius: 999px; }
        .col-count { font-family: var(--font-mono); font-size: .7rem; color: var(--rr-steel-700); padding: 2px 8px; background: var(--rr-mist); border-radius: 999px; font-weight: 600; }
        .lead-card { background: #fff; border: 1px solid var(--rr-parchment); border-radius: 6px; padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; box-shadow: 0 1px 2px rgba(10,25,47,0.04); cursor: grab; transition: box-shadow 200ms, transform 200ms, opacity 160ms; touch-action: none; }
        .lead-card:hover { box-shadow: 0 4px 14px rgba(10,25,47,0.12); transform: translateY(-1px); }
        .lead-card:active { cursor: grabbing; }
        .lead-card.selected { border-color: var(--rr-steel-500); box-shadow: 0 0 0 3px rgba(58,127,189,0.18); }
        .lead-card.dragging { opacity: 0.4; }
        .lead-card.overlay { box-shadow: 0 14px 32px rgba(10,25,47,0.22); transform: rotate(2deg); cursor: grabbing; }
        .lead-name { font-family: var(--font-ui); font-weight: 600; font-size: .9rem; color: var(--rr-navy-800); display: flex; justify-content: space-between; align-items: flex-start; gap: 6px; }
        .lead-source { font-family: var(--font-ui); font-size: .64rem; font-weight: 600; padding: 2px 8px; border-radius: 999px; letter-spacing: .04em; text-transform: uppercase; background: var(--rr-mist); color: var(--rr-steel-700); flex-shrink: 0; }
        .lead-contact { font-family: var(--font-ui); font-size: .76rem; color: var(--rr-slate-dark); display: flex; align-items: center; gap: 6px; }
        .lead-notes { font-family: var(--font-ui); font-size: .76rem; color: #4A5568; line-height: 1.4; max-height: 36px; overflow: hidden; }
        .lead-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 2px; padding-top: 8px; border-top: 1px solid var(--rr-parchment); }
        .lead-owner { display: inline-flex; align-items: center; gap: 6px; font-family: var(--font-ui); font-size: .7rem; color: var(--rr-slate-dark); }
        .avatar-mini { width: 18px; height: 18px; border-radius: 999px; background: var(--rr-steel-500); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: .58rem; font-weight: 600; }
        .drawer-tabs { display: flex; gap: 0; border-bottom: 1px solid var(--rr-parchment); margin-bottom: 14px; }
        .drawer-tab { padding: 10px 14px; font-family: var(--font-ui); font-size: .82rem; color: var(--rr-slate-dark); cursor: pointer; border-bottom: 2px solid transparent; background: none; border-top: none; border-left: none; border-right: none; }
        .drawer-tab.active { color: var(--rr-navy-800); border-bottom-color: var(--rr-steel-500); font-weight: 600; }
        .timeline-row { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--rr-parchment); }
        .timeline-row:last-child { border: none; }
        .timeline-icon { width: 28px; height: 28px; border-radius: 999px; flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center; }
        .ti-call { background: #D9EAF5; color: #2E6494; }
        .ti-email { background: #F5F2EC; color: #4A5568; }
        .ti-sms { background: #E8F5EE; color: #2A7D4F; }
        .ti-note { background: #FDF3E5; color: #B45309; }
        .ti-meeting { background: #F8E5E8; color: #9B2335; }
        .ti-body { display: flex; flex-direction: column; gap: 3px; min-width: 0; flex: 1; }
        .ti-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
        .ti-kind { font-family: var(--font-ui); font-weight: 600; font-size: .82rem; color: var(--rr-navy-800); }
        .ti-when { font-family: var(--font-mono); font-size: .68rem; color: var(--rr-slate-dark); flex-shrink: 0; }
        .ti-text { font-family: var(--font-ui); font-size: .82rem; color: var(--rr-ink); line-height: 1.5; }
      `}</style>

      <div className="page-header">
        <div>
          <h1 className="page-title">CRM</h1>
          <div className="page-sub">{leads.length} leads · {leads.filter(l => l.status === 'QUALIFIED').length} qualified</div>
        </div>
        <button className="btn btn-primary btn-md" onClick={() => setDrawerOpen(true)} data-testid="btn-new-lead">+ New lead</button>
      </div>

      <div className="kpi-row">
        <KpiTile label="Pipeline value" value="$14.2K" delta="+ $2.1K" trend="up" accent="steel" />
        <KpiTile label="Conversion" value="22%" delta="+ 2%" trend="up" accent="steel" />
        <KpiTile label="Avg days" value="18" delta="– 3" trend="up" accent="navy" />
        <KpiTile label="New this week" value={String(leads.filter(l => l.status === 'NEW').length)} delta="" trend="up" accent="steel" />
      </div>

      <DndContext sensors={sensors} onDragStart={onDragStart} onDragEnd={onDragEnd} onDragCancel={() => setActiveId(null)}>
        <div className="kanban">
          {COLUMNS.map(col => (
            <Column key={col.id} col={col} leads={colLeads(col.id)} selectedId={selectedLead?.id ?? null} onSelect={setSelectedLead} isOver={false} />
          ))}
        </div>
        <DragOverlay>
          {activeLead ? (
            <div className="lead-card overlay">
              <div className="lead-name">{activeLead.first} {activeLead.last}<span className="lead-source">{activeLead.source}</span></div>
              <div className="lead-contact"><Phone size={11} /> {activeLead.phone}</div>
              <div className="lead-notes">{activeLead.notes}</div>
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {drawerOpen && (
        <Drawer open={true} onClose={() => setDrawerOpen(false)} meta="New lead" title="Add a new lead" sub="Enter lead contact information." footer={<><button className="btn btn-ghost btn-md" onClick={() => setDrawerOpen(false)}>Cancel</button><button className="btn btn-primary btn-md" onClick={handleCreateLead} data-testid="btn-save-lead">Save lead</button></>}>
          <div className="field-row"><div className="field"><label className="lbl">First name *</label><input className="d-input" value={newFirst} onChange={e => setNewFirst(e.target.value)} data-testid="input-first" /></div><div className="field"><label className="lbl">Last name *</label><input className="d-input" value={newLast} onChange={e => setNewLast(e.target.value)} data-testid="input-last" /></div></div>
          <div className="field"><label className="lbl">Phone</label><input className="d-input" placeholder="+1 (403) 555-XXXX" value={newPhone} onChange={e => setNewPhone(e.target.value)} /></div>
          <div className="field"><label className="lbl">Email</label><input className="d-input" value={newEmail} onChange={e => setNewEmail(e.target.value)} /></div>
          <div className="field"><label className="lbl">Source</label><select className="d-input" value={newSource} onChange={e => setNewSource(e.target.value)}><option>Google</option><option>Referral</option><option>Website</option><option>Yelp</option><option>Walk-in</option><option>Insurance</option></select></div>
          <div className="field"><label className="lbl">Notes</label><textarea className="d-textarea" placeholder="Lead notes..." value={newNotes} onChange={e => setNewNotes(e.target.value)} /></div>
        </Drawer>
      )}

      {selectedLead && (
        <Drawer
          open={true}
          onClose={() => setSelectedLead(null)}
          meta="Lead detail"
          title={`${selectedLead.first} ${selectedLead.last}`}
          sub={selectedLead.id + ' · ' + selectedLead.source}
          footer={<><button className="btn btn-ghost btn-md" onClick={() => setSelectedLead(null)}>Close</button></>}
        >
          <div className="drawer-tabs">
            {['Info', 'Activity', 'Notes'].map((t, i) => (
              <button key={t} className={'drawer-tab' + (drawerTab === i ? ' active' : '')} onClick={() => setDrawerTab(i)}>{t}</button>
            ))}
          </div>

          {drawerTab === 0 && (
            <div>
              <div className="detail-row"><span className="detail-k">Name</span><span className="detail-v">{selectedLead.first} {selectedLead.last}</span></div>
              <div className="detail-row"><span className="detail-k">Phone</span><span className="detail-v" style={{ fontFamily: 'var(--font-mono)' }}>{selectedLead.phone}</span></div>
              <div className="detail-row"><span className="detail-k">Email</span><span className="detail-v">{selectedLead.email}</span></div>
              <div className="detail-row"><span className="detail-k">Source</span><span className="detail-v">{selectedLead.source}</span></div>
              <div className="detail-row"><span className="detail-k">Status</span><span className="detail-v"><StatusPill status={selectedLead.status.toLowerCase()} label={selectedLead.status} /></span></div>
            </div>
          )}

          {drawerTab === 1 && (
            <div>
              <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
                <select className="d-input" style={{ width: 100 }} value={activityKind} onChange={e => setActivityKind(e.target.value)}>
                  <option value="note">Note</option>
                  <option value="call">Call</option>
                  <option value="email">Email</option>
                  <option value="meeting">Meeting</option>
                </select>
                <input className="d-input" style={{ flex: 1 }} placeholder="Activity description..." value={activityBody} onChange={e => setActivityBody(e.target.value)} data-testid="input-activity" />
                <button className="btn btn-primary btn-sm" onClick={handleAddActivity} data-testid="btn-add-activity">Add</button>
              </div>
              {activities.map(a => {
                const icon = iconMap[a.kind] || iconMap.note;
                return (
                  <div key={a.id} className="timeline-row">
                    <div className={'timeline-icon ' + icon.cls}>{icon.el}</div>
                    <div className="ti-body">
                      <div className="ti-head">
                        <span className="ti-kind">{a.kind}</span>
                        <span className="ti-when">{new Date(a.occurred_at).toLocaleString()}</span>
                      </div>
                      <div className="ti-text">{a.body}</div>
                    </div>
                  </div>
                );
              })}
              {activities.length === 0 && <div style={{ color: '#8A9BB0', textAlign: 'center', padding: 20 }}>No activities yet</div>}
            </div>
          )}

          {drawerTab === 2 && (
            <div className="field">
              <label className="lbl">Notes</label>
              <textarea className="d-textarea" defaultValue={selectedLead.notes} />
            </div>
          )}
        </Drawer>
      )}
    </>
  );
}
