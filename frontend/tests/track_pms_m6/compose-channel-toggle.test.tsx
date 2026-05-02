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
  it('sends whatsapp channel when WhatsApp tab is selected', async () => {
    let captured: unknown;

    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json([])),
      http.get('/api/patients', () =>
        HttpResponse.json({
          items: [{ id: 'p-1', first_name: 'Alice', last_name: 'Smith', phone: '+15551112222' }],
          total: 1,
          page: 1,
          limit: 20,
        }),
      ),
      http.post('/api/v2/communications/send', async ({ request }) => {
        captured = await request.json();
        return HttpResponse.json({ id: 'msg-1', status: 'sent' }, { status: 201 });
      }),
    );

    render(<CommInbox />, { wrapper });

    // Open compose dialog
    await waitFor(() => expect(screen.getByRole('button', { name: /compose/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /compose/i }));

    // Search for and select the patient (D2 PatientSearchInput)
    await waitFor(() => expect(screen.getByPlaceholderText(/search patient/i)).toBeInTheDocument());
    fireEvent.change(screen.getByPlaceholderText(/search patient/i), { target: { value: 'Alice' } });
    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument());
    fireEvent.mouseDown(screen.getByText('Alice Smith'));

    // Activate WhatsApp tab via keyboard (Radix Tabs responds to Enter in jsdom)
    await waitFor(() => expect(screen.getByRole('tab', { name: /whatsapp/i })).toBeInTheDocument());
    const waTab = screen.getByRole('tab', { name: /whatsapp/i });
    waTab.focus();
    fireEvent.keyDown(waTab, { key: 'Enter' });

    // Type in the message body textarea
    const bodyTextarea = screen.getByRole('textbox', { name: /message body/i });
    fireEvent.change(bodyTextarea, { target: { value: 'Hello via WhatsApp' } });

    // Submit
    await waitFor(() => expect(screen.getByRole('button', { name: /^send$/i })).not.toBeDisabled());
    fireEvent.click(screen.getByRole('button', { name: /^send$/i }));

    await waitFor(() =>
      expect(captured).toMatchObject({ patient_id: 'p-1', channel: 'whatsapp', body: 'Hello via WhatsApp' }),
    );
  });
});
