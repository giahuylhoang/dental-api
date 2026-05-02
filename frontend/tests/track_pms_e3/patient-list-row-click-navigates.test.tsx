import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import PatientList from '../../src/features/patients/PatientList';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

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
  ],
  total: 1,
  page: 1,
  limit: 20,
};

describe('PatientList row click navigates (E3)', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    server.use(
      http.get('/api/patients', () => HttpResponse.json(mockPatients)),
    );
  });

  it('clicking a row calls navigate with /patients/:id', async () => {
    render(<PatientList />, { wrapper });
    const nameCell = await screen.findByText('Alice Smith');
    fireEvent.click(nameCell);
    expect(mockNavigate).toHaveBeenCalledWith('/patients/p1');
  });
});
