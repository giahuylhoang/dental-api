// BillingSummary.tsx — dental-pms.v1 reference layout
// Demonstrates: --font-mono, --color-danger, --color-success, --shadow-sm,
//               --radius-lg, --color-border-subtle, --space-*

interface BillingSummaryProps {
  subtotal: number;
  insuranceCoverage: number;
  discount?: number;
  paid: number;
}

export function BillingSummary({ subtotal, insuranceCoverage, discount = 0, paid }: BillingSummaryProps) {
  const afterInsurance = subtotal - insuranceCoverage - discount;
  const owing = afterInsurance - paid;

  return (
    <div style={{
      background: 'white',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--color-border-subtle)',
      boxShadow: 'var(--shadow-sm)',
      padding: 'var(--space-5)',
      fontFamily: 'var(--font-display)',
      minWidth: 280,
    }}>
      <div style={{ fontWeight: 600, fontSize: 'var(--text-base)', marginBottom: 'var(--space-4)', color: 'var(--color-text-primary)' }}>
        Billing summary
      </div>
      {[
        { label: 'Subtotal', value: subtotal },
        { label: 'Insurance coverage', value: -insuranceCoverage },
        ...(discount > 0 ? [{ label: 'Discount', value: -discount }] : []),
        { label: 'Paid', value: -paid },
      ].map(({ label, value }) => (
        <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
          <span>{label}</span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>{value < 0 ? `−$${Math.abs(value).toFixed(2)}` : `$${value.toFixed(2)}`}</span>
        </div>
      ))}
      <div style={{ borderTop: '1px solid var(--color-border-default)', marginTop: 'var(--space-3)', paddingTop: 'var(--space-3)', display: 'flex', justifyContent: 'space-between', fontWeight: 700 }}>
        <span style={{ fontSize: 'var(--text-base)', color: 'var(--color-text-primary)' }}>Balance owing</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-base)', color: owing > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>
          {owing > 0 ? `$${owing.toFixed(2)}` : 'Paid in full'}
        </span>
      </div>
    </div>
  );
}
