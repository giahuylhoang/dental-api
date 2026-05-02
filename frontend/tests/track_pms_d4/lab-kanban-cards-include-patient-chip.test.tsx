import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LabCaseKanban from '../../src/features/lab/LabCaseKanban';

const patient = {
  id: 'p-chip-1',
  first_name: 'Jane',
  last_name: 'Doe',
  phone: '555-0001',
  email: 'jane@example.com',
  date_of_birth: '1980-01-01',
  status: 'active',
  clinic_id: 'default',
};

const cases = [
  {
    id: 'lc-chip-1',
    case_number: 'LC-CHIP-001',
    denture_case_id: 'dc1',
    vendor_id: 'v1',
    status: 'sent',
    sent_at: null,
    due_back_at: null,
    remake_of_id: null,
    remake_reason: null,
    lab_fee: 200,
    patient_id: 'p-chip-1',
  },
];

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('lab-kanban-cards-include-patient-chip', () => {
  it('every card with a patient_id has data-testid="patient-chip"', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json(cases)),
      http.get('/api/patients/:id', ({ params }) => {
        if (params.id === 'p-chip-1') return HttpResponse.json(patient);
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
      }),
    );

    render(<LabCaseKanban />, { wrapper });

    await waitFor(() =>
      expect(screen.getAllByTestId('patient-chip').length).toBeGreaterThanOrEqual(1),
    );
  });
});
