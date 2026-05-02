interface DateTimePickerProps {
  value: Date | null;
  onChange: (d: Date) => void;
  min?: Date;
  max?: Date;
}

function toLocal(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function DateTimePicker({ value, onChange, min, max }: DateTimePickerProps) {
  return (
    <input
      type="datetime-local"
      className="rounded border px-2 py-1 text-sm"
      value={value ? toLocal(value) : ''}
      min={min ? toLocal(min) : undefined}
      max={max ? toLocal(max) : undefined}
      onChange={(e) => {
        if (e.target.value) onChange(new Date(e.target.value));
      }}
    />
  );
}
