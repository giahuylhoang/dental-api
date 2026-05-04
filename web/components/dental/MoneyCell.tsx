export interface MoneyCellProps {
  amount: number;
  negative?: boolean;
}

export function MoneyCell({ amount, negative }: MoneyCellProps) {
  const fmt = new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD" });
  return (
    <span className={`font-mono text-sm ${negative ? "text-destructive" : "text-foreground"}`}>
      {fmt.format(amount)}
    </span>
  );
}
