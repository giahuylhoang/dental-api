import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import { PatientChip } from '../../src/features/patients/PatientChip';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('PatientChip fallback on 404', () => {
  it('shows truncated id with title when patient not found', async () => {
    server.use(
      http.get('/api/patients/:id', () =>
        HttpResponse.json({ detail: 'Not found' }, { status: 404 }),
      ),
    );

    render(<PatientChip patientId="p1" />, { wrapper });
    await waitFor(() => expect(screen.getByTitle('Patient not found')).toBeInTheDocument());
    expect(screen.getByText('p1…')).toBeInTheDocument();
  });
});
