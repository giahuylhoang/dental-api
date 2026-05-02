import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LeadCreateDialog from '../../src/features/crm/LeadCreateDialog';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('LeadCreateDialog', () => {
  it('fills name+phone, clicks Save, POSTs correct body', async () => {
    let capturedBody: unknown;

    server.use(
      http.post('/api/v2/crm/leads', async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({ id: 'new-lead', ...(capturedBody as object) }, { status: 201 });
      }),
    );

    render(<LeadCreateDialog open onClose={vi.fn()} />, { wrapper });

    fireEvent.change(screen.getByLabelText('first_name'), { target: { value: 'John' } });
    fireEvent.change(screen.getByLabelText('last_name'), { target: { value: 'Doe' } });
    fireEvent.change(screen.getByLabelText('phone'), { target: { value: '555-0001' } });

    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() =>
      expect(capturedBody).toMatchObject({
        first_name: 'John',
        last_name: 'Doe',
        phone: '555-0001',
      }),
    );
  });
});
