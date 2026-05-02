// AppointmentCard.tsx — dental-pms.v1 reference layout
// Demonstrates: --radius-md, --color-warning, --color-success, --color-danger,
//               --shadow-xs, --text-sm, --space-*

type ApptStatus = 'confirmed' | 'pending' | 'cancelled' | 'completed';

interface AppointmentCardProps {
  patientName: string;
  time: string;
  duration: string;
  service: string;
  doctor: string;
  status: ApptStatus;
}

const STATUS_STYLE: Record<ApptStatus, { bg: string; color: string; label: string }> = {
  confirmed:  { bg: 'var(--ds-accent-100)',  color: 'var(--ds-accent-700)',  label: 'Confirmed' },
  pending:    { bg: 'var(--ds-warn-100)',    color: 'var(--ds-warn-700)',    label: 'Pending' },
  cancelled:  { bg: 'var(--ds-danger-100)', color: 'var(--ds-danger-700)', label: 'Cancelled' },
  completed:  { bg: 'var(--ds-clinical-200)', color: 'var(--ds-clinical-700)', label: 'Completed' },
};

export function AppointmentCard({ patientName, time, duration, service, doctor, status }: AppointmentCardProps) {
  const s = STATUS_STYLE[status];
  return (
    <div style={{
      background: 'white',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--color-border-subtle)',
      boxShadow: 'var(--shadow-xs)',
      padding: 'var(--space-4)',
      fontFamily: 'var(--font-display)',
      display: 'flex',
      gap: 'var(--space-4)',
      alignItems: 'center',
    }}>
      <div style={{ textAlign: 'center', minWidth: 56 }}>
        <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-text-primary)', lineHeight: 1 }}>{time}</div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>{duration}</div>
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)' }}>{patientName}</div>
        <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>{service} · {doctor}</div>
      </div>
      <span style={{
        padding: '2px var(--space-2)',
        borderRadius: 'var(--radius-sm)',
        fontSize: 'var(--text-xs)', fontWeight: 500,
        background: s.bg, color: s.color,
      }}>{s.label}</span>
    </div>
  );
}
