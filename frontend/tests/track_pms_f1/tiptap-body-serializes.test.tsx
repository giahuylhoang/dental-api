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

describe('Tiptap body serializes to plain text', () => {
  it('submits plain text body from the message textarea', async () => {
    let captured: unknown;

    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json([])),
      http.get('/api/patients', () =>
        HttpResponse.json({ items: [], total: 0, page: 1, limit: 20 }),
      ),
      http.post('/api/v2/communications/send', async ({ request }) => {
        captured = await request.json();
        return HttpResponse.json({ id: 'msg-1', status: 'sent' }, { status: 201 });
      }),
    );

    render(<CommInbox />, { wrapper });

    // Open compose
    await waitFor(() => expect(screen.getByRole('button', { name: /compose/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /compose/i }));

    // Fill patient id (raw query as fallback)
    await waitFor(() => expect(screen.getByPlaceholderText(/search patient/i)).toBeInTheDocument());
    fireEvent.change(screen.getByPlaceholderText(/search patient/i), { target: { value: 'p-1' } });

    // Type in the message body textarea (aria-label="message body")
    const bodyTextarea = screen.getByRole('textbox', { name: /message body/i });
    fireEvent.change(bodyTextarea, { target: { value: 'hello world' } });

    // Submit
    await waitFor(() => expect(screen.getByRole('button', { name: /^send$/i })).not.toBeDisabled());
    fireEvent.click(screen.getByRole('button', { name: /^send$/i }));

    await waitFor(() =>
      expect(captured).toMatchObject({ body: 'hello world' }),
    );
  });
});
