import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import CommInbox from '../../src/features/communications/CommInbox';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('ComposeDialog channel toggle', () => {
  it('sends whatsapp channel when WhatsApp toggle is selected', async () => {
    let captured: unknown;

    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json([])),
      http.post('/api/v2/communications/send', async ({ request }) => {
        captured = await request.json();
        return HttpResponse.json({ id: 'msg-1', status: 'sent' }, { status: 201 });
      }),
    );

    render(<CommInbox />, { wrapper });

    // Open compose dialog
    await waitFor(() => expect(screen.getByRole('button', { name: /compose/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /compose/i }));

    // Click WhatsApp toggle
    await waitFor(() => expect(screen.getByRole('button', { name: /whatsapp/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /whatsapp/i }));

    // Fill patient ID and body (inputs are identified by position in the form)
    const inputs = screen.getAllByRole('textbox');
    // inputs[0] = patient id, inputs[1] = to, inputs[2] = message (textarea)
    fireEvent.change(inputs[0], { target: { value: 'p-1' } });
    fireEvent.change(inputs[2], { target: { value: 'Hello via WhatsApp' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /^send$/i }));

    await waitFor(() =>
      expect(captured).toMatchObject({ patient_id: 'p-1', channel: 'whatsapp', body: 'Hello via WhatsApp' }),
    );
  });
});
