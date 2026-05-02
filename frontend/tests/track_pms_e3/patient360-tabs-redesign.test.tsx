import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import Patient360 from '../../src/features/patients/Patient360';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/patients/p1']}>
        <Routes>
          <Route path="/patients/:id" element={children} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const mockPatient = {
  id: 'p1',
  first_name: 'Alice',
  last_name: 'Smith',
  email: 'alice@example.com',
  phone: '555-0101',
  date_of_birth: '1975-03-15',
  status: 'active',
};

describe('Patient360 tabs redesign (E3)', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/patients/p1', () => HttpResponse.json(mockPatient)),
      http.get('/api/appointments', () => HttpResponse.json([])),
      http.get('/api/v2/clinical/patients/p1/denture-cases', () => HttpResponse.json([])),
      http.get('/api/v2/clinical/patients/p1/treatment-plans', () => HttpResponse.json([])),
      http.get('/api/v2/clinical/patients/p1/notes', () => HttpResponse.json([])),
      http.get('/api/v2/clinical/patients/p1/medical-history', () => HttpResponse.json({})),
      http.get('/api/v2/clinical/patients/p1/insurance', () => HttpResponse.json([])),
      http.get('/api/v2/clinical/patients/p1/documents', () => HttpResponse.json([])),
      http.get('/api/v2/clinical/patients/p1/lifecycle', () => HttpResponse.json({})),
      http.get('/api/v2/clinical/patients/p1/tooth-chart', () => HttpResponse.json({})),
    );
  });

  it('renders sticky header with patient-chip testid', async () => {
    render(<Patient360 />, { wrapper });
    expect(await screen.findByTestId('patient-chip')).toBeInTheDocument();
  });

  it('renders all 8 required tabs', async () => {
    render(<Patient360 />, { wrapper });
    const tabLabels = ['Overview', 'Appointments', 'Documents', 'Insurance', 'Treatment Plans', 'Lab Cases', 'Communications', 'Notes'];
    for (const label of tabLabels) {
      expect(await screen.findByRole('tab', { name: label })).toBeInTheDocument();
    }
  });
});
