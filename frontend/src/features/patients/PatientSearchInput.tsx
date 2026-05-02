import { useState, useRef, useCallback, useEffect } from 'react';
import { fetcher } from '../../api/client';
import { Skeleton } from '../../components/ui/skeleton';
import type { Patient } from './usePatient';

interface Props {
  onSelect: (patient: Patient) => void;
  placeholder?: string;
  initialValue?: string;
  autoFocus?: boolean;
}

function initials(p: Patient): string {
  return `${p.first_name.charAt(0)}${p.last_name.charAt(0)}`.toUpperCase();
}

export function PatientSearchInput({ onSelect, placeholder = 'Search patients…', initialValue = '', autoFocus }: Props) {
  const [query, setQuery] = useState(initialValue);
  const [results, setResults] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const search = useCallback(async (q: string) => {
    if (!q) { setResults([]); return; }
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetcher<{ items: Patient[] }>(`/api/patients?q=${encodeURIComponent(q)}&limit=10`);
      setResults(res.items ?? []);
    } catch {
      setError('Search failed');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => search(query), 200);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, search]);

  return (
    <div data-testid="patient-search" className="relative">
      <input
        className="w-full rounded border border-zinc-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
        placeholder={placeholder}
        value={query}
        autoFocus={autoFocus}
        onChange={(e) => setQuery(e.target.value)}
      />
      {(isLoading || results.length > 0 || (query && !isLoading)) && (
        <div className="absolute z-10 mt-1 w-full rounded border border-zinc-200 bg-white shadow-md">
          {isLoading && (
            <div className="space-y-1 p-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          )}
          {error && <p className="px-3 py-2 text-xs text-red-600">{error}</p>}
          {!isLoading && !error && results.length === 0 && query && (
            <p className="px-3 py-2 text-sm text-zinc-400">No patients found</p>
          )}
          {!isLoading && results.map((p) => (
            <button
              key={p.id}
              type="button"
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-zinc-50"
              onMouseDown={() => {
                onSelect(p);
                setQuery(`${p.first_name} ${p.last_name}`);
                setResults([]);
              }}
            >
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-500 text-xs font-medium text-white">
                {initials(p)}
              </span>
              <span className="flex flex-col">
                <span>{p.first_name} {p.last_name}</span>
                {(p.phone || p.date_of_birth) && (
                  <span className="text-xs text-zinc-500">{p.phone ?? p.date_of_birth}</span>
                )}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
