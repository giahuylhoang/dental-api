// EmptyState.tsx — dental-pms.v1 reference layout
// Demonstrates: --color-text-secondary, --color-bg-clinical, --radius-xl,
//               --text-lg, --text-sm, --space-*

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: { label: string; onClick?: () => void };
}

export function EmptyState({ icon = '📋', title, description, action }: EmptyStateProps) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-16) var(--space-8)',
      fontFamily: 'var(--font-display)',
      textAlign: 'center',
    }}>
      <div style={{
        width: 64, height: 64,
        background: 'var(--color-bg-clinical)',
        borderRadius: 'var(--radius-xl)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 28, marginBottom: 'var(--space-4)',
      }}>
        {icon}
      </div>
      <div style={{ fontSize: 'var(--text-lg)', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: 'var(--space-2)' }}>
        {title}
      </div>
      {description && (
        <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', maxWidth: 320, lineHeight: 'var(--leading-relaxed)', marginBottom: 'var(--space-6)' }}>
          {description}
        </div>
      )}
      {action && (
        <button onClick={action.onClick} style={{
          background: 'var(--color-action)', color: 'white',
          padding: 'var(--space-2) var(--space-5)',
          borderRadius: 'var(--radius-md)', border: 'none', cursor: 'pointer',
          fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', fontWeight: 500,
        }}>
          {action.label}
        </button>
      )}
    </div>
  );
}
