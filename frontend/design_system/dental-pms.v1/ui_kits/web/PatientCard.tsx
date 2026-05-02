// PatientCard.tsx — dental-pms.v1 reference layout
// Demonstrates: --shadow-sm, --radius-lg, --color-text-secondary,
//               --font-mono, --text-sm, --space-*

interface PatientCardProps {
  id: string;
  name: string;
  dob: string;
  phone: string;
  lastVisit?: string;
  balance?: number;
}

export function PatientCard({ id, name, dob, phone, lastVisit, balance = 0 }: PatientCardProps) {
  const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2);
  const balanceColor = balance > 0 ? 'var(--color-danger)' : 'var(--color-success)';

  return (
    <div style={{
      background: 'white',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border-subtle)',
      boxShadow: 'var(--shadow-sm)',
      padding: 'var(--space-5)',
      fontFamily: 'var(--font-display)',
      display: 'flex',
      gap: 'var(--space-4)',
      alignItems: 'flex-start',
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: '50%',
        background: 'var(--ds-action-100)', color: 'var(--color-action)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontWeight: 600, fontSize: 'var(--text-sm)', flexShrink: 0,
      }}>
        {initials}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--color-text-primary)' }}>{name}</div>
        <div style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)' }}>{id}</div>
        <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)' }}>
          DOB: {dob} · {phone}
        </div>
        {lastVisit && (
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-1)' }}>
            Last visit: {lastVisit}
          </div>
        )}
      </div>
      {balance !== 0 && (
        <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: balanceColor, flexShrink: 0 }}>
          {balance > 0 ? `$${balance.toFixed(2)} owing` : 'Paid'}
        </div>
      )}
    </div>
  );
}
