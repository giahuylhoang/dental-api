// Header.tsx — dental-pms.v1 reference layout
// Demonstrates: --font-display, --color-bg-clinical, --color-border-subtle,
//               --color-text-primary, --color-text-secondary, --space-*, --shadow-sm

export function Header({ clinicName = 'Maple Dental', userName = 'Dr. Chen' }) {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: 'var(--space-3) var(--space-6)',
      background: 'white',
      borderBottom: '1px solid var(--color-border-subtle)',
      boxShadow: 'var(--shadow-xs)',
      fontFamily: 'var(--font-display)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <img src="../../assets/logo.svg" alt={clinicName} style={{ height: 28 }} />
        <span style={{ fontWeight: 600, fontSize: 'var(--text-base)', color: 'var(--color-text-primary)' }}>
          {clinicName}
        </span>
      </div>
      <nav style={{ display: 'flex', gap: 'var(--space-1)' }}>
        {['Dashboard', 'Schedule', 'Patients', 'Billing'].map(item => (
          <a key={item} href="#" style={{
            padding: 'var(--space-2) var(--space-3)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--text-sm)',
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
            textDecoration: 'none',
          }}>{item}</a>
        ))}
      </nav>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>{userName}</span>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: 'var(--ds-action-100)', color: 'var(--color-action)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 'var(--text-sm)', fontWeight: 600,
        }}>
          {userName.split(' ').map(w => w[0]).join('')}
        </div>
      </div>
    </header>
  );
}
