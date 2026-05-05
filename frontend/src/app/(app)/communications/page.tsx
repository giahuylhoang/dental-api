'use client';

import React, { useEffect, useState } from 'react';
import { useToast } from '@/components/overlays/ToastContext';
import { Drawer } from '@/components/overlays/Drawer';
import { Search, Send } from 'lucide-react';
import { api, PatientDTO } from '@/lib/api';

type Channel = 'sms' | 'email' | 'whatsapp';

interface CommDTO {
  id: string;
  patient_id: string;
  channel: string;
  direction: string;
  body: string;
  status: string;
  thread_key: string;
  read_at: string | null;
  created_at: string;
}

interface Thread {
  id: string;
  patient: string;
  patient_id: string;
  channel: Channel;
  preview: string;
  when: string;
  unread: number;
  phone: string;
  messages: CommDTO[];
}

const channelIcons: Record<Channel, { cls: string; label: string }> = {
  sms: { cls: 'ch-sms', label: 'SMS' },
  email: { cls: 'ch-email', label: 'Email' },
  whatsapp: { cls: 'ch-whatsapp', label: 'WhatsApp' },
};

const TEMPLATE_BODIES: Record<string, (firstName: string) => string> = {
  'Appointment reminder': (n) => `Hi ${n}, this is Oak Dental Calgary. Your appointment is confirmed for Friday. Reply YES to confirm or call us at 403-555-0180.`,
  'Recall notice': (n) => `Hi ${n}, it's been 6 months since your last visit. Book your recall appointment: 403-555-0180.`,
  'Invoice ready': (n) => `Hi ${n}, your invoice is ready. Pay online or at your next visit.`,
};

export default function CommunicationsPage() {
  const { addToast } = useToast();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [patients, setPatients] = useState<PatientDTO[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [channelFilter, setChannelFilter] = useState<Channel | null>(null);
  const [search, setSearch] = useState('');
  const [composeChannel, setComposeChannel] = useState<Channel>('sms');
  const [composeText, setComposeText] = useState('');
  const [loading, setLoading] = useState(true);

  const [newOpen, setNewOpen] = useState(false);
  const [newPatientId, setNewPatientId] = useState<string>('');
  const [newChannel, setNewChannel] = useState<Channel>('sms');
  const [newSubject, setNewSubject] = useState('');
  const [newBody, setNewBody] = useState('');

  const fetchData = async () => {
    try {
      const [comms, pts] = await Promise.all([
        api.v2.communications.list() as Promise<CommDTO[]>,
        api.patients.list(),
      ]);
      setPatients(pts);
      if (pts.length && !newPatientId) setNewPatientId(pts[0].id);

      // Group by thread_key
      const byThread = new Map<string, CommDTO[]>();
      for (const c of comms) {
        const key = c.thread_key || c.id;
        if (!byThread.has(key)) byThread.set(key, []);
        byThread.get(key)!.push(c);
      }

      const threadList: Thread[] = [];
      for (const [key, msgs] of byThread) {
        const latest = msgs[0];
        const patient = pts.find(p => p.id === latest.patient_id);
        const patientName = patient ? `${patient.first_name || ''} ${patient.last_name || ''}`.trim() : 'Unknown';
        threadList.push({
          id: key,
          patient: patientName,
          patient_id: latest.patient_id,
          channel: (latest.channel as Channel) || 'sms',
          preview: latest.body?.slice(0, 80) || '',
          when: new Date(latest.created_at).toLocaleTimeString(),
          unread: msgs.filter(m => !m.read_at && m.direction === 'in').length,
          phone: patient?.phone || patient?.email || '',
          messages: msgs,
        });
      }
      setThreads(threadList);
      if (threadList.length && !activeId) setActiveId(threadList[0].id);
    } catch (e) {
      console.error('Failed to load communications', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const activeThread = threads.find(t => t.id === activeId) ?? threads[0];

  const filtered = threads.filter(t => {
    if (channelFilter && t.channel !== channelFilter) return false;
    if (search && !t.patient.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const handleSend = async () => {
    if (!composeText.trim() || !activeThread) return;
    try {
      await api.v2.communications.send({
        patient_id: activeThread.patient_id,
        channel: composeChannel,
        body: composeText,
      });
      addToast('Message sent.', `${activeThread.patient} · ${composeChannel.toUpperCase()}`);
      setComposeText('');
      await fetchData();
    } catch (e) {
      addToast('Failed to send message.', '');
    }
  };

  const handleMarkRead = async (threadKey: string) => {
    try {
      await api.v2.communications.threadRead(threadKey);
      await fetchData();
    } catch {}
  };

  const templates = ['Appointment reminder', 'Recall notice', 'Invoice ready'];

  const applyTemplate = (tpl: string) => {
    const fn = TEMPLATE_BODIES[tpl];
    if (fn && activeThread) setComposeText(fn(activeThread.patient.split(' ')[0]));
  };

  const applyNewTemplate = (tpl: string) => {
    const fn = TEMPLATE_BODIES[tpl];
    if (!fn) return;
    const p = patients.find(p => p.id === newPatientId);
    if (p) setNewBody(fn(p.first_name || 'Patient'));
  };

  const openNewMessage = () => {
    if (patients.length) setNewPatientId(patients[0].id);
    setNewChannel('sms');
    setNewSubject('');
    setNewBody('');
    setNewOpen(true);
  };

  const sendNewMessage = async () => {
    const patient = patients.find(p => p.id === newPatientId);
    if (!patient || !newBody.trim()) {
      addToast('Add a recipient and message body.', '');
      return;
    }
    try {
      await api.v2.communications.send({
        patient_id: newPatientId,
        channel: newChannel,
        body: newBody,
      });
      setNewOpen(false);
      addToast('Message sent.', `${patient.first_name} ${patient.last_name} · ${newChannel.toUpperCase()}`);
      await fetchData();
    } catch (e) {
      addToast('Failed to send message.', '');
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <>
      <style>{`
        .inbox { display: grid; grid-template-columns: 340px 1fr; gap: 0; background: #fff; border: 1px solid var(--rr-parchment); border-radius: 6px; box-shadow: var(--shadow-xs); overflow: hidden; min-height: 700px; }
        .inbox-left { border-right: 1px solid var(--rr-parchment); display: flex; flex-direction: column; }
        .inbox-right { display: flex; flex-direction: column; min-width: 0; }
        .left-head { padding: 14px 16px; border-bottom: 1px solid var(--rr-parchment); display: flex; flex-direction: column; gap: 10px; }
        .channel-chips { display: flex; gap: 6px; flex-wrap: wrap; }
        .chip { height: 28px; padding: 0 10px; border-radius: 999px; border: 1px solid var(--rr-parchment); background: #fff; font-family: var(--font-ui); font-size: .72rem; color: var(--rr-slate-dark); cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
        .chip.active { background: var(--rr-navy-800); color: #fff; border-color: var(--rr-navy-800); font-weight: 600; }
        .chip-count { background: rgba(255,255,255,0.18); color: inherit; padding: 1px 6px; border-radius: 999px; font-family: var(--font-mono); font-size: .65rem; }
        .thread-list { flex: 1; overflow-y: auto; }
        .thread-row { padding: 12px 16px; border-bottom: 1px solid var(--rr-parchment); cursor: pointer; display: flex; flex-direction: column; gap: 5px; transition: background 150ms; }
        .thread-row:hover { background: var(--rr-warm-white); }
        .thread-row.active { background: var(--rr-mist); border-left: 3px solid var(--rr-steel-500); padding-left: 13px; }
        .thread-row .top { display: flex; justify-content: space-between; align-items: center; }
        .thread-row .pname { font-family: var(--font-ui); font-weight: 600; font-size: .88rem; color: var(--rr-navy-800); }
        .thread-row .when { font-family: var(--font-mono); font-size: .68rem; color: var(--rr-slate-dark); }
        .thread-row .preview-line { display: flex; align-items: center; gap: 6px; }
        .ch-icon { width: 18px; height: 18px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 10px; }
        .ch-sms { background: #D9EAF5; color: #2E6494; }
        .ch-email { background: #F5F2EC; color: #4A5568; }
        .ch-whatsapp { background: #E8F5EE; color: #2A7D4F; }
        .thread-row .preview { flex: 1; font-family: var(--font-ui); font-size: .78rem; color: var(--rr-slate-dark); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .unread-dot { min-width: 18px; height: 18px; border-radius: 999px; background: var(--rr-steel-500); color: #fff; font-size: .65rem; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }
        .right-head { padding: 14px 18px; border-bottom: 1px solid var(--rr-parchment); display: flex; justify-content: space-between; align-items: center; }
        .right-head .who { display: flex; align-items: center; gap: 10px; }
        .avatar-sm { width: 36px; height: 36px; border-radius: 999px; background: var(--rr-steel-500); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-family: var(--font-ui); font-weight: 600; font-size: .82rem; }
        .right-head .rname { font-family: var(--font-display); font-weight: 700; font-size: 1rem; color: var(--rr-navy-800); }
        .right-head .rmeta { font-family: var(--font-ui); font-size: .72rem; color: var(--rr-slate-dark); margin-top: 2px; }
        .messages { flex: 1; overflow-y: auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; background: var(--rr-warm-white); }
        .day-divider { display: flex; align-items: center; gap: 10px; margin: 6px 0; }
        .day-divider::before, .day-divider::after { content: ''; flex: 1; height: 1px; background: var(--rr-parchment); }
        .day-divider span { font-family: var(--font-ui); font-size: .68rem; color: var(--rr-slate-dark); letter-spacing: .08em; text-transform: uppercase; }
        .msg { max-width: 70%; padding: 10px 14px; border-radius: 12px; font-family: var(--font-ui); font-size: .88rem; line-height: 1.5; box-shadow: 0 1px 2px rgba(10,25,47,0.05); }
        .msg.in { background: #fff; border: 1px solid var(--rr-parchment); color: var(--rr-ink); align-self: flex-start; border-bottom-left-radius: 4px; }
        .msg.out { background: var(--rr-navy-800); color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }
        .msg-meta { font-family: var(--font-mono); font-size: .66rem; color: var(--rr-slate-dark); margin-top: 4px; }
        .composer { padding: 14px 18px; border-top: 1px solid var(--rr-parchment); display: flex; flex-direction: column; gap: 10px; background: #fff; }
        .composer-channel-tabs { display: inline-flex; gap: 4px; }
        .composer-channel-tabs .ct { height: 28px; padding: 0 10px; font-family: var(--font-ui); font-size: .72rem; color: var(--rr-slate-dark); cursor: pointer; border-radius: 4px; border: none; background: none; }
        .composer-channel-tabs .ct.active { background: var(--rr-mist); color: var(--rr-navy-800); font-weight: 600; }
        .composer textarea { width: 100%; min-height: 56px; max-height: 160px; padding: 10px 12px; border: 1px solid var(--rr-parchment); border-radius: 6px; font-family: var(--font-ui); font-size: .88rem; color: var(--rr-ink); resize: vertical; box-sizing: border-box; }
        .composer-bottom { display: flex; justify-content: space-between; align-items: center; }
        .templates { display: flex; gap: 6px; flex-wrap: wrap; }
        .templates .tpl { font-family: var(--font-ui); font-size: .7rem; color: var(--rr-steel-700); background: var(--rr-mist); padding: 4px 10px; border-radius: 999px; cursor: pointer; border: none; }
      `}</style>

      <div className="page-header">
        <div>
          <h1 className="page-title">Communications</h1>
          <div className="page-sub">{threads.length} threads · {threads.filter(t => t.unread > 0).length} unread</div>
        </div>
        <button className="btn btn-primary btn-md" onClick={openNewMessage} data-testid="btn-new-message">+ New message</button>
      </div>

      <div className="inbox">
        <div className="inbox-left">
          <div className="left-head">
            <div className="channel-chips">
              <button className={'chip' + (!channelFilter ? ' active' : '')} onClick={() => setChannelFilter(null)}>
                All <span className="chip-count">{threads.length}</span>
              </button>
              {(['sms', 'email', 'whatsapp'] as const).map(ch => (
                <button key={ch} className={'chip' + (channelFilter === ch ? ' active' : '')} onClick={() => setChannelFilter(channelFilter === ch ? null : ch)}>
                  {channelIcons[ch].label} <span className="chip-count">{threads.filter(t => t.channel === ch).length}</span>
                </button>
              ))}
            </div>
            <div className="left-search" style={{ position: 'relative' }}>
              <Search size={12} strokeWidth={1.6} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#8A9BB0' }} />
              <input placeholder="Search patients..." value={search} onChange={e => setSearch(e.target.value)}
                style={{ flex: 1, height: 34, padding: '0 10px 0 32px', borderRadius: 4, border: '1px solid #EDE9E0', background: '#FAF9F6', fontFamily: 'var(--font-ui)', fontSize: '.82rem', color: 'var(--rr-ink)', width: '100%' }} />
            </div>
          </div>
          <div className="thread-list">
            {filtered.length === 0 && <div style={{ padding: 20, textAlign: 'center', color: '#8A9BB0' }}>No threads yet</div>}
            {filtered.map(t => (
              <div key={t.id} className={'thread-row' + (activeThread?.id === t.id ? ' active' : '')} onClick={() => { setActiveId(t.id); if (t.unread > 0) handleMarkRead(t.id); }}>
                <div className="top">
                  <span className="pname">{t.patient}</span>
                  <span className="when">{t.when}</span>
                </div>
                <div className="preview-line">
                  <span className={'ch-icon ' + channelIcons[t.channel]?.cls}>{channelIcons[t.channel]?.label?.[0] || '?'}</span>
                  <span className="preview">{t.preview}</span>
                  {t.unread > 0 && <span className="unread-dot">{t.unread}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="inbox-right">
          {activeThread ? (
            <>
              <div className="right-head">
                <div className="who">
                  <div className="avatar-sm">{activeThread.patient.split(' ').map(s => s[0]).join('')}</div>
                  <div>
                    <div className="rname">{activeThread.patient}</div>
                    <div className="rmeta">{activeThread.phone} · {channelIcons[activeThread.channel]?.label}</div>
                  </div>
                </div>
              </div>

              <div className="messages">
                <div className="day-divider"><span>Today</span></div>
                {activeThread.messages.slice().reverse().map(m => (
                  <div key={m.id} className={`msg ${m.direction === 'in' ? 'in' : 'out'}`}>
                    {m.body}
                    <div className="msg-meta" style={m.direction === 'out' ? { color: 'rgba(255,255,255,0.5)' } : {}}>
                      {new Date(m.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>

              <div className="composer">
                <div className="composer-channel-tabs">
                  {(['sms', 'email', 'whatsapp'] as const).map(ch => (
                    <button key={ch} className={'ct' + (composeChannel === ch ? ' active' : '')} onClick={() => setComposeChannel(ch)}>
                      {channelIcons[ch].label}
                    </button>
                  ))}
                </div>
                <textarea placeholder="Type your message..." value={composeText} onChange={e => setComposeText(e.target.value)} data-testid="compose-textarea" />
                <div className="composer-bottom">
                  <div className="templates">
                    {templates.map(t => (
                      <button key={t} className="tpl" onClick={() => applyTemplate(t)}>{t}</button>
                    ))}
                  </div>
                  <button className="btn btn-primary btn-sm" onClick={handleSend} data-testid="btn-send">
                    <Send size={14} /> Send
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8A9BB0' }}>
              Select a thread or start a new message
            </div>
          )}
        </div>
      </div>

      {newOpen && (
        <Drawer
          open={true}
          onClose={() => setNewOpen(false)}
          meta="New message"
          title="Compose message"
          sub="Pick a recipient, channel, and write your message."
          footer={
            <>
              <button className="btn btn-ghost btn-md" onClick={() => setNewOpen(false)}>Cancel</button>
              <button className="btn btn-primary btn-md" onClick={sendNewMessage} data-testid="btn-send-new">Send</button>
            </>
          }
        >
          <div className="field">
            <label className="lbl">Recipient</label>
            <select className="d-input" value={newPatientId} onChange={e => setNewPatientId(e.target.value)}>
              {patients.map(p => (
                <option key={p.id} value={p.id}>{p.first_name} {p.last_name} · {p.id}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label className="lbl">Channel</label>
            <div className="composer-channel-tabs" style={{ gap: 6 }}>
              {(['sms', 'email', 'whatsapp'] as const).map(ch => (
                <button
                  key={ch}
                  className={'ct' + (newChannel === ch ? ' active' : '')}
                  style={{ border: '1px solid var(--rr-parchment)', minWidth: 80 }}
                  onClick={() => setNewChannel(ch)}
                >
                  {channelIcons[ch].label}
                </button>
              ))}
            </div>
          </div>
          {newChannel === 'email' && (
            <div className="field">
              <label className="lbl">Subject</label>
              <input className="d-input" value={newSubject} onChange={e => setNewSubject(e.target.value)} placeholder="e.g. Appointment confirmation" />
            </div>
          )}
          <div className="field">
            <label className="lbl">Message</label>
            <textarea className="d-textarea" value={newBody} onChange={e => setNewBody(e.target.value)} placeholder="Type your message..." style={{ minHeight: 140 }} data-testid="new-body-textarea" />
          </div>
          <div className="field">
            <label className="lbl">Templates</label>
            <div className="templates">
              {templates.map(t => (
                <button key={t} className="tpl" onClick={() => applyNewTemplate(t)}>{t}</button>
              ))}
            </div>
          </div>
        </Drawer>
      )}
    </>
  );
}
