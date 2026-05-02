// ProcedureRow.tsx — dental-pms.v1 reference layout
// Demonstrates: --font-mono, --color-border-subtle, --text-sm, --space-*

interface ProcedureRowProps {
  code: string;
  description: string;
  tooth?: string;
  fee: number;
  insuranceCoverage?: number;
  status?: 'planned' | 'completed' | 'in-progress';
}

const STATUS_COLOR: Record<string, string> = {
  planned:     'var(--color-text-secondary)',
  completed:   'var(--color-success)',
  'in-progress': 'var(--color-warning)',
};

export function ProcedureRow({ code, description, tooth, fee, insuranceCoverage = 0, status = 'planned' }: ProcedureRowProps) {
  const patientOwes = fee - insuranceCoverage;
  return (
    <tr style={{ fontFamily: 'var(--font-display)', borderBottom: '1px solid var(--color-border-subtle)' }}>
      <td style={{ padding: 'var(--space-3) var(--space-4)', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>
        {code}
      </td>
      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)' }}>
        {description}
      </td>
      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-mono)' }}>
        {tooth ?? '—'}
      </td>
      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-sm)', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
        ${fee.toFixed(2)}
      </td>
      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-sm)', textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
        ${insuranceCoverage.toFixed(2)}
      </td>
      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-sm)', textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
        ${patientOwes.toFixed(2)}
      </td>
      <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-xs)', color: STATUS_COLOR[status] }}>
        {status}
      </td>
    </tr>
  );
}
