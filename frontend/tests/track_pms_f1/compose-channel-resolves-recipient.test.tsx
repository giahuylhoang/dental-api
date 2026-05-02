import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import CommInbox from '../../src/features/communications/CommInbox';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const patient = { id: 'p-test', first_name: 'Test', last_name: 'User', phone: '+15551234567', email: 'a@x.com' };

describe('ComposeDialog channel resolves recipient', () => {
  it('auto-fills to from patient phone/email based on channel', async () => {
    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json([])),
      http.get('/api/patients', () =>
        HttpResponse.json({ items: [patient], total: 1, page: 1, limit: 20 }),
      ),
    );

    render(<CommInbox />, { wrapper });

    // Open compose
    await waitFor(() => expect(screen.getByRole('button', { name: /compose/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /compose/i }));

    // Select patient
    await waitFor(() => expect(screen.getByPlaceholderText(/search patient/i)).toBeInTheDocument());
    fireEvent.change(screen.getByPlaceholderText(/search patient/i), { target: { value: 'test' } });
    await waitFor(() => expect(screen.getByText('Test User')).toBeInTheDocument());
    fireEvent.mouseDown(screen.getByText('Test User'));

    // Default channel is SMS → to = phone
    await waitFor(() => expect(screen.getByDisplayValue('+15551234567')).toBeInTheDocument());

    // Scope to compose dialog to avoid ambiguity with filter chips
    const dialog = screen.getByRole('heading', { name: /new message/i }).closest('div.w-96')!;
    const compose = within(dialog);

    // Switch to Email → to = email
    fireEvent.click(compose.getByRole('button', { name: /^email$/i }));
    await waitFor(() => expect(screen.getByDisplayValue('a@x.com')).toBeInTheDocument());

    // Switch to WhatsApp → to = phone
    fireEvent.click(compose.getByRole('button', { name: /^whatsapp$/i }));
    await waitFor(() => expect(screen.getByDisplayValue('+15551234567')).toBeInTheDocument());
  });
});
