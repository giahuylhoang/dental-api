import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LabCaseKanban from '../../src/features/lab/LabCaseKanban';

const STATUSES = ['draft', 'sent', 'in_progress', 'returned', 'remake'] as const;

const patient = {
  id: 'p-e4-1',
  first_name: 'Alice',
  last_name: 'Smith',
  phone: '555-0001',
  email: 'alice@example.com',
  date_of_birth: '1985-01-01',
  status: 'active',
  clinic_id: 'default',
};

const cases = STATUSES.map((status, i) => ({
  id: `lc-e4-${i}`,
  case_number: `LC-E4-${String(i + 1).padStart(4, '0')}`,
  denture_case_id: 'dc1',
  vendor_id: 'v1',
  status,
  sent_at: null,
  due_back_at: '2026-05-10T00:00:00Z',
  lab_fee: 300,
  remake_of_id: null,
  remake_reason: null,
  treatment_plan_id: null,
  patient_id: 'p-e4-1',
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('lab-tp-redesign', () => {
  it('renders ≥5 columns', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json(cases)),
      http.get('/api/patients/:id', () => HttpResponse.json(patient)),
    );

    render(<LabCaseKanban />, { wrapper });

    await waitFor(() => {
      // 5 column headers
      const headers = screen.getAllByRole('heading', { level: 3 });
      expect(headers.length).toBeGreaterThanOrEqual(5);
    });
  });

  it('each card has data-testid="patient-chip"', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json(cases)),
      http.get('/api/patients/:id', () => HttpResponse.json(patient)),
    );

    render(<LabCaseKanban />, { wrapper });

    await waitFor(() => {
      const chips = screen.getAllByTestId('patient-chip');
      expect(chips.length).toBeGreaterThanOrEqual(5);
    });
  });

  it('cards use D1 Card component (rounded-lg border class present)', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json(cases)),
      http.get('/api/patients/:id', () => HttpResponse.json(patient)),
    );

    const { container } = render(<LabCaseKanban />, { wrapper });

    await waitFor(() => {
      // D1 Card has rounded-lg border classes from shadcn card
      const cards = container.querySelectorAll('.rounded-lg.border');
      expect(cards.length).toBeGreaterThanOrEqual(5);
    });
  });
});
