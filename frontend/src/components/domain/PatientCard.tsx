import { Patient } from '@/lib/data';
import Link from 'next/link';

interface PatientCardProps {
  patient: Patient;
  density?: 'comfortable' | 'compact';
  onClick?: () => void;
}

export function PatientCard({ patient, density = 'comfortable', onClick }: PatientCardProps) {
  const initials = ((patient.first?.[0] || '?') + (patient.last?.[0] || '?')).toUpperCase();
  const compact = density === 'compact';
  const colorByStatus: Record<string, string> = { 
    active: '#3A7FBD', recall: '#B45309', plan: '#6BAED6', inactive: '#8A9BB0' 
  };
  const bg = colorByStatus[patient.status] || '#3A7FBD';

  const statusTone: Record<string, { bg: string; fg: string }> = {
    active: { bg: '#E8F5EE', fg: '#2A7D4F' },
    recall: { bg: '#FDF3E5', fg: '#B45309' },
    plan: { bg: '#F5F2EC', fg: '#4A5568' },
    inactive: { bg: '#F5F2EC', fg: '#8A9BB0' },
  };
  const tone = statusTone[patient.status] || statusTone.active;

  return (
    <div
      onClick={onClick}
      style={{
        background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6,
        padding: compact ? '12px 14px' : '16px 18px',
        boxShadow: '0 1px 2px rgba(10,25,47,0.06)',
        display: 'grid', gridTemplateColumns: '40px 1fr auto', gap: 14, alignItems: 'center',
        cursor: 'pointer', transition: 'box-shadow 200ms ease, border-color 200ms ease',
      }}
      onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 4px 20px rgba(10,25,47,0.12)'; }}
      onMouseLeave={e => { e.currentTarget.style.boxShadow = '0 1px 2px rgba(10,25,47,0.06)'; }}
    >
      <div style={{
        width: 40, height: 40, borderRadius: 999, background: bg, color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.82rem',
      }}>{initials}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
        <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.92rem', color: '#1C2333', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {patient.first} {patient.last}
        </div>
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.7rem', color: '#8A9BB0', display: 'flex', gap: 8 }}>
          <span>{patient.id}</span>
          <span>·</span>
          <span>{patient.dob}</span>
          <span>·</span>
          <span style={{ fontFamily: "'Inter', sans-serif", color: '#4A5568' }}>{patient.insurance}</span>
        </div>
      </div>
      <span style={{
        fontSize: '0.66rem', fontWeight: 600, padding: '3px 10px', borderRadius: 999,
        letterSpacing: '0.06em', textTransform: 'uppercase',
        background: tone.bg, color: tone.fg,
      }}>{patient.status}</span>
    </div>
  );
}
