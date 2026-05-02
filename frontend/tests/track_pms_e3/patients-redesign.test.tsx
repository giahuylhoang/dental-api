import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import PatientList from '../../src/features/patients/PatientList';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

const mockPatients = {
  items: [
    { id: 'p1', first_name: 'Alice', last_name: 'Smith', phone: '555-0101', date_of_birth: '1975-03-15', status: 'active', email: 'alice@example.com' },
    { id: 'p2', first_name: 'Bob', last_name: 'Jones', phone: '555-0102', date_of_birth: '1960-07-22', status: 'active', email: 'bob@example.com' },
  ],
  total: 2,
  page: 1,
  limit: 20,
};

describe('PatientList redesign (E3)', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/patients', () => HttpResponse.json(mockPatients)),
    );
  });

  it('renders PageHeader with title "Patients"', async () => {
    render(<PatientList />, { wrapper });
    expect(await screen.findByText('Patients')).toBeInTheDocument();
  });

  it('renders search input with testid', async () => {
    render(<PatientList />, { wrapper });
    expect(await screen.findByTestId('patient-search')).toBeInTheDocument();
  });

  it('renders DataTable rows for patients', async () => {
    render(<PatientList />, { wrapper });
    expect(await screen.findByText('Alice Smith')).toBeInTheDocument();
    expect(await screen.findByText('Bob Jones')).toBeInTheDocument();
  });

  it('renders "+ New patient" button', async () => {
    render(<PatientList />, { wrapper });
    expect(await screen.findByRole('button', { name: /new patient/i })).toBeInTheDocument();
  });
});
