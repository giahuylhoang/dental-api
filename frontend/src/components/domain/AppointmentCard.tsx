import { Appointment } from '@/lib/data';

const STATUS_TONE: Record<string, { bg: string; fg: string; label: string }> = {
  confirmed: { bg: '#E8F5EE', fg: '#2A7D4F', label: 'Confirmed' },
  pending:   { bg: '#FDF3E5', fg: '#B45309', label: 'Pending' },
  no_show:   { bg: '#F8E5E8', fg: '#9B2335', label: 'No-show' },
  completed: { bg: '#F5F2EC', fg: '#4A5568', label: 'Completed' },
  cancelled: { bg: '#EDE9E0', fg: '#4A5568', label: 'Cancelled' },
};

interface AppointmentCardProps {
  appointment: Appointment;
  expanded?: boolean;
  onClick?: () => void;
}

export function AppointmentCard({ appointment, expanded, onClick }: AppointmentCardProps) {
  const a = appointment;
  const tone = STATUS_TONE[a.status] || STATUS_TONE.confirmed;
  const initials = a.patient.split(' ').map(s => s[0]).slice(0, 2).join('');

  return (
    <div
      onClick={onClick}
      style={{
        background: '#fff',
        border: expanded ? '1.5px solid #3A7FBD' : '1px solid #EDE9E0',
        borderRadius: 6,
        padding: '14px 16px',
        display: 'grid',
        gridTemplateColumns: '64px 32px 1fr auto',
        gap: 14, alignItems: 'center',
        transition: 'box-shadow 200ms ease, border-color 200ms ease',
        cursor: 'pointer',
        boxShadow: expanded ? '0 4px 20px rgba(10,25,47,0.12)' : 'none',
      }}
      onMouseEnter={e => { if (!expanded) e.currentTarget.style.boxShadow = '0 2px 8px rgba(10,25,47,0.08)'; }}
      onMouseLeave={e => { if (!expanded) e.currentTarget.style.boxShadow = 'none'; }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, fontSize: '1rem', color: '#0A192F' }}>{a.time}</span>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.7rem', color: '#8A9BB0' }}>{a.duration} min</span>
      </div>
      <div style={{ width: 32, height: 32, borderRadius: 999, background: '#3A7FBD', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: '0.7rem' }}>{initials.toUpperCase()}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
        <span style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.88rem', color: '#1C2333' }}>{a.patient}</span>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.74rem', color: '#4A5568' }}>{a.kind} · {a.provider} · Op {a.chair}</span>
      </div>
      <span style={{ fontSize: '0.66rem', fontWeight: 600, padding: '3px 10px', borderRadius: 4, letterSpacing: '0.06em', textTransform: 'uppercase', background: tone.bg, color: tone.fg }}>{tone.label}</span>
    </div>
  );
}
