import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { PatientSearchInput } from './PatientSearchInput';
import type { Patient as SearchPatient } from './usePatient';

interface Patient {
  id: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  date_of_birth?: string | null;
  status?: string;
}

interface PatientsPage {
  items: Patient[];
  total: number;
  page: number;
  limit: number;
}

export default function PatientList() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const limit = 20;

  const { data, isLoading } = useQuery<PatientsPage>({
    queryKey: ['patients', page],
    queryFn: async () => {
      const arr = await fetcher<Patient[]>(`/api/patients`);
      const start = (page - 1) * limit;
      return { items: arr.slice(start, start + limit), total: arr.length, page, limit };
    },
  });

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Patients</h2>
      </div>
      <div className="mb-4 max-w-sm">
        <PatientSearchInput
          onSelect={(p: SearchPatient) => navigate(`/patients/${p.id}`)}
          placeholder="Search by name, phone, or email…"
        />
      </div>
      {isLoading ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-left text-zinc-500">
                <th className="pb-2 pr-4 font-medium">Name</th>
                <th className="pb-2 pr-4 font-medium">Phone</th>
                <th className="pb-2 pr-4 font-medium">Email</th>
                <th className="pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((p) => (
                <tr key={p.id} className="border-b border-zinc-100 hover:bg-zinc-50">
                  <td className="py-2 pr-4">
                    <Link to={`/patients/${p.id}`} className="font-medium text-zinc-900 hover:underline">
                      {p.first_name} {p.last_name}
                    </Link>
                  </td>
                  <td className="py-2 pr-4 text-zinc-600">{p.phone ?? '—'}</td>
                  <td className="py-2 pr-4 text-zinc-600">{p.email ?? '—'}</td>
                  <td className="py-2">
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                      active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.total > limit && (
            <div className="mt-4 flex gap-2 text-sm">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded border px-3 py-1 disabled:opacity-40"
              >
                Prev
              </button>
              <span className="py-1 text-zinc-500">
                Page {page} of {Math.ceil(data.total / limit)}
              </span>
              <button
                disabled={page >= Math.ceil(data.total / limit)}
                onClick={() => setPage((p) => p + 1)}
                className="rounded border px-3 py-1 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
