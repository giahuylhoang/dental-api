import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import type { components } from '../../api/v2/types';

type Document = components['schemas']['Document'];

interface DocumentListProps {
  patientId: string;
  kindFilter?: string;
}

const KIND_LABELS: Record<string, string> = {
  photo: 'Photos',
  xray: 'X-Rays',
  consent: 'Consent Forms',
  other: 'Other',
};

export default function DocumentList({ patientId, kindFilter }: DocumentListProps) {
  const { data: docs = [], isLoading } = useQuery<Document[]>({
    queryKey: ['documents', patientId],
    queryFn: () => fetcher<Document[]>(`/api/v2/clinical/patients/${patientId}/documents`),
  });

  if (isLoading) return <p className="text-sm text-zinc-500">Loading…</p>;

  const filtered = kindFilter ? docs.filter((d) => d.kind === kindFilter) : docs;
  if (filtered.length === 0) return <p className="text-sm text-zinc-500">No documents.</p>;

  const grouped = filtered.reduce<Record<string, Document[]>>((acc, doc) => {
    const k = doc.kind;
    if (!acc[k]) acc[k] = [];
    acc[k].push(doc);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([kind, items]) => (
        <div key={kind}>
          <h4 className="mb-2 text-sm font-medium text-zinc-700">{KIND_LABELS[kind] ?? kind}</h4>
          <div className="space-y-1">
            {items.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between rounded border border-zinc-200 px-3 py-2 text-sm">
                <a
                  href={doc.storage_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-zinc-900 hover:underline"
                >
                  {doc.storage_url.split('/').pop() ?? doc.id}
                </a>
                <div className="flex items-center gap-3 text-zinc-500">
                  <span>{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '—'}</span>
                  <span>{doc.size_bytes ? `${(doc.size_bytes / 1024).toFixed(1)} KB` : '—'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
