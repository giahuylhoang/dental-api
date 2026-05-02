import { useEffect, useState, useCallback, useRef } from 'react';
import { Command } from 'cmdk';
import { useNavigate } from 'react-router-dom';
import { getRecent, markVisited } from './recentlyViewed';
import { fetcher } from '../../api/client';
import type { Patient } from '../patients/usePatient';

interface PaletteItem {
  id: string;
  label: string;
  section: string;
  onSelect: () => void;
}

function initials(p: Patient): string {
  return `${p.first_name.charAt(0)}${p.last_name.charAt(0)}`.toUpperCase();
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [patients, setPatients] = useState<Patient[]>([]);
  const navigate = useNavigate();
  const recent = getRecent();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const close = useCallback(() => {
    setOpen(false);
    setQuery('');
    setPatients([]);
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') close();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [close]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      if (!query) { setPatients([]); return; }
      try {
        const res = await fetcher<{ items: Patient[] }>(`/api/patients?q=${encodeURIComponent(query)}&limit=5`);
        setPatients(res.items ?? []);
      } catch {
        setPatients([]);
      }
    }, 200);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query]);

  const quickActions: PaletteItem[] = [
    { id: 'new-invoice', label: 'New invoice', section: 'Quick actions', onSelect: () => { navigate('/billing'); close(); } },
    { id: 'new-appointment', label: 'New appointment', section: 'Quick actions', onSelect: () => { navigate('/schedule'); close(); } },
    { id: 'new-lead', label: 'New lead', section: 'Quick actions', onSelect: () => { navigate('/crm'); close(); } },
  ];

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      className="fixed inset-0 z-50 flex items-start justify-center pt-24"
      onClick={close}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-zinc-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <Command>
          <Command.Input
            value={query}
            onValueChange={setQuery}
            placeholder="Search patients, invoices, appointments…"
            className="w-full border-b border-zinc-200 px-4 py-3 text-sm outline-none"
          />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            {patients.length > 0 && (
              <Command.Group heading="Patients">
                {patients.map((p) => {
                  const label = `${p.first_name} ${p.last_name}`;
                  return (
                    <Command.Item
                      key={p.id}
                      value={label}
                      onSelect={() => {
                        markVisited('patient', p.id, label);
                        navigate(`/patients/${p.id}`);
                        close();
                      }}
                      className="cursor-pointer rounded px-3 py-2 text-sm hover:bg-zinc-100 aria-selected:bg-zinc-100"
                    >
                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-xs font-medium text-white mr-2">
                        {initials(p)}
                      </span>
                      <span>{label}</span>
                      {p.phone && <span className="ml-2 text-xs text-zinc-500">{p.phone}</span>}
                    </Command.Item>
                  );
                })}
              </Command.Group>
            )}

            {!query && recent.length > 0 && (
              <Command.Group heading="Recently viewed">
                {recent.map((item) => (
                  <Command.Item
                    key={`${item.kind}-${item.id}`}
                    value={`${item.label} ${item.kind}`}
                    onSelect={() => {
                      markVisited(item.kind, item.id, item.label);
                      navigate(`/${item.kind}s/${item.id}`);
                      close();
                    }}
                    className="cursor-pointer rounded px-3 py-2 text-sm hover:bg-zinc-100 aria-selected:bg-zinc-100"
                  >
                    {item.label}
                  </Command.Item>
                ))}
              </Command.Group>
            )}

            <Command.Group heading="Quick actions">
              {quickActions.map((a) => (
                <Command.Item
                  key={a.id}
                  value={a.label}
                  onSelect={a.onSelect}
                  className="cursor-pointer rounded px-3 py-2 text-sm hover:bg-zinc-100 aria-selected:bg-zinc-100"
                >
                  {a.label}
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
