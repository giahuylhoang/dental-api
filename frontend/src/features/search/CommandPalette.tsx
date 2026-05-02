import { useEffect, useState, useCallback } from 'react';
import { Command } from 'cmdk';
import { useNavigate } from 'react-router-dom';
import { getRecent, markVisited } from './recentlyViewed';

interface PaletteItem {
  id: string;
  label: string;
  section: string;
  onSelect: () => void;
}

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const recent = getRecent();

  const close = useCallback(() => {
    setOpen(false);
    setQuery('');
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
            {recent.length > 0 && (
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
