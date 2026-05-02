import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { type ColumnDef } from '@tanstack/react-table';
import { fetcher } from '../../api/client';
import { PatientSearchInput } from './PatientSearchInput';
import { PageHeader } from '../../components/ui/page-header';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import { DataTable } from '../../components/ui/data-table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import QuickBookPopover from './QuickBookPopover';
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

function initials(p: Patient) {
  return `${(p.first_name ?? '?').charAt(0)}${(p.last_name ?? '?').charAt(0)}`.toUpperCase();
}

export default function PatientList() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('active');
  const [newPatientOpen, setNewPatientOpen] = useState(false);
  const limit = 20;

  const { data, isLoading } = useQuery<PatientsPage>({
    queryKey: ['patients', page],
    queryFn: () => fetcher<PatientsPage>(`/api/patients?page=${page}&limit=${limit}`),
  });

  const activeCount = data?.items.filter((p) => (p.status ?? 'active') === 'active').length ?? 0;

  const filtered = (data?.items ?? []).filter((p) => {
    if (statusFilter === 'all') return true;
    return (p.status ?? 'active') === statusFilter;
  });

  const columns: ColumnDef<Patient>[] = [
    {
      accessorKey: 'name',
      header: 'Name',
      cell: ({ row }) => {
        const p = row.original;
        return (
          <span className="inline-flex items-center gap-2">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-blue-500 text-xs font-medium text-white">
              {initials(p)}
            </span>
            <span className="font-medium">{p.first_name} {p.last_name}</span>
          </span>
        );
      },
    },
    {
      accessorKey: 'phone',
      header: 'Phone',
      cell: ({ row }) => row.original.phone ?? '—',
    },
    {
      accessorKey: 'date_of_birth',
      header: 'DOB',
      cell: ({ row }) => row.original.date_of_birth ?? '—',
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const s = row.original.status ?? 'active';
        return (
          <Badge variant={s === 'active' ? 'default' : 'secondary'}>
            {s}
          </Badge>
        );
      },
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" onClick={(e) => e.stopPropagation()}>⋯</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => navigate(`/patients/${row.original.id}`)}>View</DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate(`/patients/${row.original.id}`)}>Edit</DropdownMenuItem>
            <DropdownMenuItem>Archive</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const totalPages = Math.ceil((data?.total ?? 0) / limit);

  return (
    <div>
      <PageHeader
        title="Patients"
        description={`${activeCount} active`}
        actions={
          <Button onClick={() => setNewPatientOpen(true)}>+ New patient</Button>
        }
      />

      <Card className="mb-4">
        <CardContent className="flex flex-wrap items-center gap-3 pt-4">
          <div className="flex-1 min-w-48">
            <PatientSearchInput
              onSelect={(p: SearchPatient) => navigate(`/patients/${p.id}`)}
              placeholder="Search by name, phone, or email…"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
              <SelectItem value="all">All</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {isLoading ? (
        <p className="text-sm text-zinc-500">Loading…</p>
      ) : filtered.length === 0 ? (
        <p className="py-12 text-center text-sm text-zinc-500">No patients found.</p>
      ) : (
        <>
          <DataTable
            columns={columns}
            data={filtered}
            onRowClick={(p) => navigate(`/patients/${p.id}`)}
          />
          {totalPages > 1 && (
            <div className="mt-4 flex items-center gap-2 text-sm">
              <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
                Prev
              </Button>
              <span className="text-zinc-500">Page {page} of {totalPages}</span>
              <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next
              </Button>
            </div>
          )}
        </>
      )}

      <Dialog open={newPatientOpen} onOpenChange={setNewPatientOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New patient</DialogTitle>
          </DialogHeader>
          <QuickBookPopover
            onCreated={() => setNewPatientOpen(false)}
            onClose={() => setNewPatientOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
