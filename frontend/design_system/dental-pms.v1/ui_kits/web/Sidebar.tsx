// Sidebar.tsx — dental-pms.v1 reference layout
// Demonstrates: --color-bg-clinical, --color-border-subtle, --color-action,
//               --space-*, --text-sm, --radius-md

const NAV_ITEMS = [
  { label: 'Dashboard', icon: '⊞' },
  { label: 'Schedule', icon: '📅' },
  { label: 'Patients', icon: '👤' },
  { label: 'Billing', icon: '💳' },
  { label: 'Reports', icon: '📊' },
  { label: 'Settings', icon: '⚙' },
];

export function Sidebar({ activeItem = 'Dashboard' }) {
  return (
    <aside style={{
      width: 220,
      minHeight: '100vh',
      background: 'var(--color-bg-clinical)',
      borderRight: '1px solid var(--color-border-subtle)',
      padding: 'var(--space-4) var(--space-3)',
      fontFamily: 'var(--font-display)',
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-1)',
    }}>
      {NAV_ITEMS.map(({ label, icon }) => {
        const active = label === activeItem;
        return (
          <a key={label} href="#" style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            padding: 'var(--space-2) var(--space-3)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--text-sm)',
            fontWeight: active ? 600 : 400,
            color: active ? 'var(--color-action)' : 'var(--color-text-secondary)',
            background: active ? 'var(--ds-action-50)' : 'transparent',
            textDecoration: 'none',
            transition: 'background var(--duration-base) var(--ease-out)',
          }}>
            <span>{icon}</span>
            {label}
          </a>
        );
      })}
    </aside>
  );
}
