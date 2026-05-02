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

const alice = { id: 'alice-1', first_name: 'Alice', last_name: 'Johnson', phone: '+15550001', email: 'alice@test.com' };

describe('ComposeDialog patient autocomplete', () => {
  it('shows dropdown with Alice when typing "ali" and sets patient_id on click', async () => {
    let captured: unknown;

    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json([])),
      http.get('/api/patients', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q') ?? '';
        const items = q.toLowerCase().includes('ali') ? [alice] : [];
        return HttpResponse.json({ items, total: items.length, page: 1, limit: 20 });
      }),
      http.post('/api/v2/communications/send', async ({ request }) => {
        captured = await request.json();
        return HttpResponse.json({ id: 'msg-1', status: 'sent' }, { status: 201 });
      }),
    );

    render(<CommInbox />, { wrapper });

    // Open compose
    await waitFor(() => expect(screen.getByRole('button', { name: /compose/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /compose/i }));

    // Type in patient search
    await waitFor(() => expect(screen.getByPlaceholderText(/search patient/i)).toBeInTheDocument());
    fireEvent.change(screen.getByPlaceholderText(/search patient/i), { target: { value: 'ali' } });

    // Dropdown shows Alice
    await waitFor(() => expect(screen.getByText('Alice Johnson')).toBeInTheDocument());

    // Click Alice
    fireEvent.mouseDown(screen.getByText('Alice Johnson'));

    // patient_id state is alice-1 — verify by submitting
    await waitFor(() => expect(screen.getByRole('button', { name: /^send$/i })).not.toBeDisabled());
    fireEvent.click(screen.getByRole('button', { name: /^send$/i }));

    await waitFor(() =>
      expect(captured).toMatchObject({ patient_id: 'alice-1' }),
    );
  });
});
