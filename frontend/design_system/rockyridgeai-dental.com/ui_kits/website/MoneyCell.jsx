// MoneyCell — CAD currency formatter in mono font
const MoneyCell = ({ amount, negative }) => {
  const fmt = new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' });
  return (
    <span style={{
      fontFamily: 'var(--font-mono)', fontSize: '.82rem',
      color: negative ? '#9B2335' : 'inherit',
    }}>
      {fmt.format(amount)}
    </span>
  );
};

window.MoneyCell = MoneyCell;
