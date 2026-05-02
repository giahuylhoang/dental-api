import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';
import LabCaseKanban from '../../src/features/lab/LabCaseKanban';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

const cases = [
  { id: 'lc-t1', case_number: 'LC-2026-0001', denture_case_id: 'dc1', vendor_id: 'v1', status: 'draft', sent_at: null, due_back_at: null, lab_fee: null, remake_of_id: null, remake_reason: null, treatment_plan_id: null },
  { id: 'lc-t2', case_number: 'LC-2026-0002', denture_case_id: 'dc1', vendor_id: 'v1', status: 'sent', sent_at: null, due_back_at: null, lab_fee: null, remake_of_id: null, remake_reason: null, treatment_plan_id: null },
  { id: 'lc-t3', case_number: 'LC-2026-0003', denture_case_id: 'dc1', vendor_id: 'v1', status: 'in_progress', sent_at: null, due_back_at: null, lab_fee: null, remake_of_id: null, remake_reason: null, treatment_plan_id: null },
];

describe('case-number-visible-on-card', () => {
  it('renders case_number pill on each kanban card', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json(cases)),
    );

    render(<LabCaseKanban />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('LC-2026-0001')).toBeInTheDocument();
      expect(screen.getByText('LC-2026-0002')).toBeInTheDocument();
      expect(screen.getByText('LC-2026-0003')).toBeInTheDocument();
    });
  });
});
