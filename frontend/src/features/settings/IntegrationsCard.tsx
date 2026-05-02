import { useState } from 'react';

interface Integration {
  enabled: boolean;
}

interface Props {
  integrations: {
    sms: Integration;
    email: Integration;
    whatsapp: Integration;
  };
}

function StatusDot({ enabled }: { enabled: boolean }) {
  return (
    <span
      data-testid={enabled ? 'dot-enabled' : 'dot-disabled'}
      className={`inline-block h-2.5 w-2.5 rounded-full ${enabled ? 'bg-green-500' : 'bg-red-500'}`}
    />
  );
}

const ROWS: { key: keyof Props['integrations']; label: string }[] = [
  { key: 'sms', label: 'SMS' },
  { key: 'email', label: 'Email' },
  { key: 'whatsapp', label: 'WhatsApp' },
];

export default function IntegrationsCard({ integrations }: Props) {
  const [open, setOpen] = useState(true);

  return (
    <div className="rounded-lg border border-zinc-200">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left font-semibold"
        onClick={() => setOpen((o) => !o)}
      >
        Integrations
        <span>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="flex flex-col gap-2 px-4 pb-4">
          {ROWS.map(({ key, label }) => (
            <div key={key} className="flex items-center gap-2 text-sm">
              <StatusDot enabled={integrations[key].enabled} />
              <span>{label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
