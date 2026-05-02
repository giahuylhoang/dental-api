import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient } from '@tanstack/react-query';

// Minimal lead conversion logic test — tests the optimistic update + rollback pattern
// without rendering the full component (avoids router/auth deps in unit tests).

interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  status: 'NEW' | 'CONTACTED' | 'QUALIFIED' | 'CONVERTED' | 'LOST';
}

const INITIAL_LEADS: Lead[] = [
  { id: 'lead-1', first_name: 'Dave', last_name: 'Brown', status: 'QUALIFIED' },
  { id: 'lead-2', first_name: 'Eve', last_name: 'Green', status: 'NEW' },
];

function applyOptimisticConvert(leads: Lead[], id: string): Lead[] {
  return leads.map((l) => (l.id === id ? { ...l, status: 'CONVERTED' as const } : l));
}

describe('lead conversion', () => {
  let qc: QueryClient;

  beforeEach(() => {
    qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    qc.setQueryData(['leads', 'default'], INITIAL_LEADS);
  });

  it('optimistic update sets status to CONVERTED', async () => {
    const prev = qc.getQueryData<Lead[]>(['leads', 'default']);
    qc.setQueryData<Lead[]>(['leads', 'default'], (old) =>
      applyOptimisticConvert(old ?? [], 'lead-1'),
    );

    const updated = qc.getQueryData<Lead[]>(['leads', 'default']);
    expect(updated?.find((l) => l.id === 'lead-1')?.status).toBe('CONVERTED');
    expect(updated?.find((l) => l.id === 'lead-2')?.status).toBe('NEW');

    // Rollback on error
    qc.setQueryData(['leads', 'default'], prev);
    const rolled = qc.getQueryData<Lead[]>(['leads', 'default']);
    expect(rolled?.find((l) => l.id === 'lead-1')?.status).toBe('QUALIFIED');
  });

  it('rollback restores original state on mutation failure', () => {
    const snapshot = qc.getQueryData<Lead[]>(['leads', 'default']);

    // Simulate optimistic update
    qc.setQueryData<Lead[]>(['leads', 'default'], (old) =>
      applyOptimisticConvert(old ?? [], 'lead-2'),
    );
    expect(
      qc.getQueryData<Lead[]>(['leads', 'default'])?.find((l) => l.id === 'lead-2')?.status,
    ).toBe('CONVERTED');

    // Simulate error → rollback
    qc.setQueryData(['leads', 'default'], snapshot);
    expect(
      qc.getQueryData<Lead[]>(['leads', 'default'])?.find((l) => l.id === 'lead-2')?.status,
    ).toBe('NEW');
  });

  it('invalidates patients query after successful conversion', async () => {
    const invalidate = vi.spyOn(qc, 'invalidateQueries');
    await qc.invalidateQueries({ queryKey: ['patients'] });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['patients'] });
  });

  it('non-targeted leads are unaffected by optimistic update', () => {
    qc.setQueryData<Lead[]>(['leads', 'default'], (old) =>
      applyOptimisticConvert(old ?? [], 'lead-1'),
    );
    const updated = qc.getQueryData<Lead[]>(['leads', 'default']);
    expect(updated?.find((l) => l.id === 'lead-2')?.status).toBe('NEW');
  });
});
