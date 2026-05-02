import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import { PatientChip } from '../../src/features/patients/PatientChip';

const alice = { id: 'p1', first_name: 'Alice', last_name: 'Smith', phone: '555-0101', email: 'alice@example.com', date_of_birth: '1975-03-15', status: 'active', clinic_id: 'default' };

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('PatientChip renders name', () => {
  it('shows Alice Smith after loading', async () => {
    server.use(
      http.get('/api/patients/:id', ({ params }) => {
        if (params.id === 'p1') return HttpResponse.json(alice);
        return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
      }),
    );

    render(<PatientChip patientId="p1" />, { wrapper });
    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument());
    expect(screen.getByTestId('patient-chip')).toBeInTheDocument();
  });
});
