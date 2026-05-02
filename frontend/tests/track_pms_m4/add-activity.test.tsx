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

describe('AddActivityForm', () => {
  it('submits note body and list refreshes', async () => {
    let capturedBody: unknown;
    const activitiesAfter = [
      { id: 'act-1', kind: 'note', body: 'First call done', author: 'Me', created_at: new Date().toISOString() },
    ];

    server.use(
      http.get('/api/v2/crm/leads/L1', () =>
        HttpResponse.json({
          id: 'L1', first_name: 'Alice', last_name: 'Smith',
          phone: null, email: null, status: 'NEW', source: null, notes: null, owner_id: null, clinic_id: 'default',
        }),
      ),
      http.get('/api/providers', () => HttpResponse.json([])),
      http.get('/api/v2/crm/leads/L1/activities', () => HttpResponse.json([])),
      http.post('/api/v2/crm/leads/L1/activities', async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json(activitiesAfter[0], { status: 201 });
      }),
    );

    render(<LeadDrawer open leadId="L1" onClose={() => {}} />, { wrapper });

    // Switch to activities tab
    await waitFor(() => expect(screen.getByRole('button', { name: /activities/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /activities/i }));

    await waitFor(() => expect(screen.getByLabelText('body')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText('body'), { target: { value: 'First call done' } });
    fireEvent.click(screen.getByRole('button', { name: /add/i }));

    await waitFor(() =>
      expect(capturedBody).toMatchObject({ kind: 'note', body: 'First call done' }),
    );
  });
});
