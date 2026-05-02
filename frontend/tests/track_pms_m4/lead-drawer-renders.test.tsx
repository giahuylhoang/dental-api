import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LeadDrawer from '../../src/features/crm/LeadDrawer';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('LeadDrawer renders', () => {
  it('shows lead name and activities tab', async () => {
    server.use(
      http.get('/api/v2/crm/leads/L1', () =>
        HttpResponse.json({
          id: 'L1',
          first_name: 'Alice',
          last_name: 'Smith',
          phone: '555-1234',
          email: null,
          status: 'NEW',
          source: 'web',
          notes: null,
          owner_id: null,
          clinic_id: 'default',
        }),
      ),
      http.get('/api/providers', () => HttpResponse.json([])),
      http.get('/api/v2/crm/leads/L1/activities', () => HttpResponse.json([])),
    );

    render(<LeadDrawer open leadId="L1" onClose={() => {}} />, { wrapper });

    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument());

    expect(screen.getByRole('button', { name: /activities/i })).toBeInTheDocument();

    // Switch to activities tab
    fireEvent.click(screen.getByRole('button', { name: /activities/i }));
    await waitFor(() => expect(screen.getByText(/no activities yet/i)).toBeInTheDocument());
  });
});
