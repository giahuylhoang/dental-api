import { describe, it, expect } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LeadKanban from '../../src/features/crm/LeadKanban';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('drag-fires-correct-status-endpoint', () => {
  it('PUT /api/v2/crm/leads/{id} when drag-end fires', async () => {
    let capturedUrl = '';
    let capturedMethod = '';
    let capturedBody: unknown;

    server.use(
      http.get('/api/v2/crm/leads', () =>
        HttpResponse.json([{
          id: 'L-drag',
          first_name: 'Drag',
          last_name: 'Test',
          phone: null,
          email: null,
          status: 'NEW',
          source: null,
          notes: null,
          owner_id: null,
          clinic_id: 'default',
        }]),
      ),
      http.put('/api/v2/crm/leads/:id', async ({ request, params }) => {
        capturedUrl = `/api/v2/crm/leads/${params.id}`;
        capturedMethod = request.method;
        capturedBody = await request.json();
        return HttpResponse.json({ id: params.id });
      }),
    );

    render(<LeadKanban />, { wrapper });

    // Wait for the lead card to appear
    await waitFor(() => expect(screen.getByText('Drag Test')).toBeInTheDocument());

    // Find the card and CONTACTED column
    const card = screen.getByText('Drag Test').closest('[draggable]')!;

    // Find CONTACTED column — it's the div with bg-blue-50
    const contactedCol = document.querySelector('.bg-blue-50')!;

    // Simulate drag sequence: dragstart sets state, drop triggers mutation
    await act(async () => {
      fireEvent.dragStart(card);
    });

    await act(async () => {
      fireEvent.dragOver(contactedCol, { preventDefault: () => {} });
      fireEvent.drop(contactedCol, { preventDefault: () => {} });
    });

    await waitFor(() => {
      expect(capturedUrl).toBe('/api/v2/crm/leads/L-drag');
      expect(capturedMethod).toBe('PUT');
      expect(capturedBody).toMatchObject({ status: 'CONTACTED' });
    });

    // Ensure old endpoint is NOT used
    expect(capturedUrl).not.toContain('/api/leads/');
    expect(capturedUrl).not.toContain('/status');
  });
});
