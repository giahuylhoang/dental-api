'use client';

import React, { useState } from 'react';
import { KpiTile } from '@/components/dental/KpiTile';
import { LockedFeature } from '@/components/dental/LockedFeature';
import styles from './page.module.css';

type Channel = 'sms' | 'email' | 'whatsapp';

const CHANNEL_LABEL: Record<Channel, string> = { sms: 'SMS', email: 'Email', whatsapp: 'WhatsApp' };

const CHANNEL_ICON: Record<Channel, React.ReactNode> = {
  sms: (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  email: (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
      <polyline points="22,6 12,13 2,6"/>
    </svg>
  ),
  whatsapp: (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
    </svg>
  ),
};

const THREADS = [
  {
    key: 't1', patient: 'Priya Khanna', patient_id: 'P-018501', channel: 'sms' as Channel, unread: 2, last_at: '08:42',
    subject: '+1 (403) 555-0182',
    messages: [
      { dir: 'out', body: 'Hi Priya — confirming your crown seat for May 4 at 9:30am. Reply YES to confirm or call us to reschedule.', at: '2026-05-03 14:00', status: 'delivered' },
      { dir: 'in',  body: 'Yes, see you then! One question — do I need to fast before this appointment?', at: '2026-05-03 14:08', status: 'received' },
      { dir: 'out', body: 'No fasting needed. Eat normally beforehand. The crown seat takes about 60 minutes.', at: '2026-05-03 14:11', status: 'delivered' },
      { dir: 'in',  body: 'Perfect, thanks. See you Saturday.', at: '08:38', status: 'received' },
      { dir: 'in',  body: 'Actually — is there parking validation?', at: '08:42', status: 'received' },
    ],
  },
  {
    key: 't2', patient: 'Marcus Doan', patient_id: 'P-018342', channel: 'email' as Channel, unread: 1, last_at: '07:11',
    subject: 'mdoan@example.com',
    messages: [
      { dir: 'out', body: 'Lab note · denture reline ETA May 8.', at: '2026-04-25 10:00', status: 'delivered' },
      { dir: 'in',  body: 'Got it. Will the appointment be the same length as before?', at: '07:11', status: 'received' },
    ],
  },
  {
    key: 't3', patient: 'Sofía Castillo', patient_id: 'P-018612', channel: 'whatsapp' as Channel, unread: 0, last_at: 'Yest',
    subject: '+1 (587) 555-0214',
    messages: [
      { dir: 'in',  body: 'Hello — just checking in about the implant follow-up.', at: 'Yest 16:20', status: 'received' },
      { dir: 'out', body: 'Hi Sofía! Healing looks excellent on imaging. Next visit is May 4 at 11:00.', at: 'Yest 16:42', status: 'delivered' },
    ],
  },
  {
    key: 't4', patient: 'Eli Brouwer', patient_id: 'P-018400', channel: 'sms' as Channel, unread: 0, last_at: '2 d',
    subject: '+1 (780) 555-0099',
    messages: [
      { dir: 'out', body: 'Eli — your retainer is back from Apex Ortho Lab. Pickup any time.', at: '2 d 09:30', status: 'delivered' },
      { dir: 'in',  body: 'Will swing by Friday morning, thanks!', at: '2 d 13:00', status: 'received' },
    ],
  },
  {
    key: 't5', patient: 'Daniel Okafor', patient_id: 'P-018450', channel: 'email' as Channel, unread: 0, last_at: '3 d',
    subject: 'd.okafor@example.com',
    messages: [
      { dir: 'in',  body: 'Inquiry about a new patient consult — what should I bring?', at: '3 d 11:14', status: 'received' },
      { dir: 'out', body: 'Welcome! Please bring photo ID, insurance card, and any imaging from previous providers.', at: '3 d 11:42', status: 'delivered' },
    ],
  },
  {
    key: 't6', patient: 'Yuki Tanaka', patient_id: 'P-018380', channel: 'whatsapp' as Channel, unread: 0, last_at: '4 d',
    subject: '+1 (403) 555-0367',
    messages: [
      { dir: 'in',  body: 'Bridge ETA update?', at: '4 d 08:00', status: 'received' },
      { dir: 'out', body: "Pinnacle flagged a delay — new ETA May 6. We'll call to rebook.", at: '4 d 09:14', status: 'delivered' },
    ],
  },
];

const TEMPLATES = ['Recall reminder', 'Confirm tomorrow', 'Lab returned', 'Balance due', 'Insurance update'];

export default function CommunicationsPage() {
  const [channel, setChannel] = useState<'all' | Channel>('all');
  const [active, setActive] = useState('t1');

  const filtered = THREADS.filter(t => channel === 'all' || t.channel === channel);
  const thread = THREADS.find(t => t.key === active) || THREADS[0];

  const totalUnread = THREADS.reduce((s, t) => s + t.unread, 0);
  const counts = {
    all: THREADS.length,
    sms: THREADS.filter(t => t.channel === 'sms').length,
    email: THREADS.filter(t => t.channel === 'email').length,
    whatsapp: THREADS.filter(t => t.channel === 'whatsapp').length,
  };

  return (
    <div className={styles.body}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Communications</h1>
          <div className={styles.pageSub}>{totalUnread} unread · {THREADS.length} active threads · SMS · email · WhatsApp · all in one inbox</div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-ghost btn-md">Templates</button>
          <button className="btn btn-ghost btn-md">Bulk recall blast</button>
          <button className="btn btn-primary btn-md">+ Compose</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        <KpiTile label="Inbound today"  value="14"  delta="+ 5"   trend="up" accent="steel" />
        <KpiTile label="Sent today"     value="38"  delta="+ 12"  trend="up" accent="steel" />
        <KpiTile label="Recall replies" value="9"   delta="+ 3"   trend="up" accent="steel" />
        <KpiTile label="Avg response"   value="6 m" delta="– 2 m" trend="up" accent="navy"  />
      </div>

      <div className={styles.inbox}>
        {/* Left: thread list */}
        <div className={styles.inboxLeft}>
          <div className={styles.leftHead}>
            <div className={styles.leftSearch}>
              <input type="search" placeholder="Search messages…" />
            </div>
            <div className={styles.channelChips}>
              {(['all', 'sms', 'email', 'whatsapp'] as const).map(c => (
                <button
                  key={c}
                  className={`${styles.chip}${channel === c ? ' ' + styles.chipActive : ''}`}
                  onClick={() => setChannel(c)}
                >
                  {c === 'all' ? 'All' : CHANNEL_LABEL[c]}
                  <span className={styles.chipCount}>{counts[c]}</span>
                </button>
              ))}
            </div>
          </div>

          <div className={styles.threadList}>
            {filtered.map(t => {
              const last = t.messages[t.messages.length - 1];
              return (
                <div
                  key={t.key}
                  className={`${styles.threadRow}${active === t.key ? ' ' + styles.threadRowActive : ''}`}
                  onClick={() => setActive(t.key)}
                >
                  <div className={styles.threadTop}>
                    <span className={styles.threadName}>{t.patient}</span>
                    <span className={styles.threadWhen}>{t.last_at}</span>
                  </div>
                  <div className={styles.previewLine}>
                    <span className={`${styles.chIcon} ${styles['ch_' + t.channel]}`}>{CHANNEL_ICON[t.channel]}</span>
                    <span className={styles.preview}>{last.dir === 'out' ? 'You: ' : ''}{last.body}</span>
                    {t.unread > 0 && <span className={styles.unreadDot}>{t.unread}</span>}
                  </div>
                </div>
              );
            })}
            {filtered.length === 0 && (
              <div className={styles.emptyState}>No threads in this channel</div>
            )}
          </div>
        </div>

        {/* Right: thread detail */}
        <div className={styles.inboxRight}>
          <div className={styles.rightHead}>
            <div className={styles.who}>
              <span className={styles.avatarSm}>
                {thread.patient.split(' ').map(s => s[0]).slice(0, 2).join('')}
              </span>
              <div>
                <div className={styles.rightName}>{thread.patient}</div>
                <div className={styles.rightMeta}>
                  <span style={{ color: '#3A7FBD', fontWeight: 600 }}>{CHANNEL_LABEL[thread.channel]}</span>
                  <span style={{ margin: '0 6px' }}>·</span>
                  <span>{thread.subject}</span>
                  <span style={{ margin: '0 6px' }}>·</span>
                  <span>{thread.patient_id} · Manulife</span>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-ghost btn-sm">Open chart</button>
              <button className="btn btn-ghost btn-sm">Mute</button>
              <button className="btn btn-ghost btn-sm">Archive</button>
            </div>
          </div>

          <div className={styles.messages}>
            <div className={styles.dayDivider}><span>{thread.messages[0].at.split(' ')[0]}</span></div>
            {thread.messages.map((m, i) => (
              <React.Fragment key={i}>
                <div className={`${styles.msg} ${m.dir === 'out' ? styles.msgOut : styles.msgIn}`}>{m.body}</div>
                <div className={styles.msgMeta} style={{ alignSelf: m.dir === 'out' ? 'flex-end' : 'flex-start' }}>
                  {m.dir === 'out' ? `Sent · ${m.at}` : m.at}
                  {m.dir === 'out' && m.status && <span style={{ color: '#2A7D4F' }}> · {m.status}</span>}
                </div>
              </React.Fragment>
            ))}
          </div>

          {/* Composer — locked per design decision */}
          <div className={styles.composer}>
            <LockedFeature
              title="Composer"
              body="The composer is paused while we redesign the templating layer."
              backHref="/communications"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
