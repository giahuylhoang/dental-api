import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

describe('assign owner', () => {
  it('changes owner dropdown and Save PUTs with owner_id', async () => {
    let capturedBody: unknown;

    server.use(
      http.get('/api/v2/crm/leads/L1', () =>
        HttpResponse.json({
          id: 'L1', first_name: 'Alice', last_name: 'Smith',
          phone: null, email: null, status: 'NEW', source: null, notes: null, owner_id: null, clinic_id: 'default',
        }),
      ),
      http.get('/api/providers', () =>
        HttpResponse.json([
          { id: 'prov-1', name: 'Dr. Johnson', is_active: true },
        ]),
      ),
      http.get('/api/v2/crm/leads/L1/activities', () => HttpResponse.json([])),
      http.put('/api/v2/crm/leads/L1', async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({ id: 'L1', ...(capturedBody as object) });
      }),
    );

    render(<LeadDrawer open leadId="L1" onClose={() => {}} />, { wrapper });

    await waitFor(() => expect(screen.getByLabelText('owner_id')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('owner_id'), { target: { value: 'prov-1' } });
    fireEvent.click(screen.getByRole('button', { name: /^save$/i }));

    await waitFor(() =>
      expect(capturedBody).toMatchObject({ owner_id: 'prov-1' }),
    );
  });
});
