import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LabCaseKanban from '../../src/features/lab/LabCaseKanban';

const alice = { id: 'p1', first_name: 'Alice', last_name: 'Smith', phone: '555-0101', email: 'alice@example.com', date_of_birth: '1975-03-15', status: 'active', clinic_id: 'default' };

const labCase = {
  id: 'lc-test',
  case_number: 'LC-TEST-001',
  denture_case_id: 'dc1',
  vendor_id: 'v1',
  status: 'sent',
  sent_at: null,
  due_back_at: null,
  returned_at: null,
  remake_of_id: null,
  remake_reason: null,
  lab_fee: 100,
  courier_tracking: null,
  clinic_id: 'default',
  patient_id: 'p1',
};

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('LabCaseKanban shows patient chip on card', () => {
  it('renders patient name chip on card when patient_id is set', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json([labCase])),
      http.get('/api/patients/:id', ({ params }) => {
        if (params.id === 'p1') return HttpResponse.json(alice);
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
      }),
    );

    render(<LabCaseKanban />, { wrapper });
    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument());
  });
});
