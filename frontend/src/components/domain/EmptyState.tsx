interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '48px 24px', gap: 12,
      textAlign: 'center',
    }}>
      {icon && <div style={{ color: '#8A9BB0', marginBottom: 8 }}>{icon}</div>}
      <div style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1.1rem', color: '#1C2333' }}>{title}</div>
      {description && <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.88rem', color: '#4A5568', maxWidth: 400 }}>{description}</div>}
      {action && <div style={{ marginTop: 8 }}>{action}</div>}
    </div>
  );
}
