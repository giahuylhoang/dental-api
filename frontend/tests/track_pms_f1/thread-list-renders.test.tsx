import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import CommInbox from '../../src/features/communications/CommInbox';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const now = new Date().toISOString();

const messages = [
  // Thread 1: Alice SMS
  { id: 'm1', patient_id: 'p1', patient_name: 'Alice', channel: 'sms', direction: 'inbound', body: 'Hello from Alice', status: 'received', created_at: now, thread_key: 'p1:sms', read_at: null, from: '+15551111' },
  { id: 'm2', patient_id: 'p1', patient_name: 'Alice', channel: 'sms', direction: 'outbound', body: 'Hi Alice!', status: 'sent', created_at: now, thread_key: 'p1:sms', read_at: now },
  // Thread 2: Bob email
  { id: 'm3', patient_id: 'p2', patient_name: 'Bob', channel: 'email', direction: 'inbound', body: 'Bob email message', status: 'received', created_at: now, thread_key: 'p2:email', read_at: null, from: 'bob@example.com' },
  // Thread 3: Carol WhatsApp
  { id: 'm4', patient_id: 'p3', patient_name: 'Carol', channel: 'whatsapp', direction: 'inbound', body: 'Carol whatsapp msg', status: 'received', created_at: now, thread_key: 'p3:whatsapp', read_at: null, from: '+15553333' },
  { id: 'm5', patient_id: 'p3', patient_name: 'Carol', channel: 'whatsapp', direction: 'inbound', body: 'Another from Carol', status: 'received', created_at: now, thread_key: 'p3:whatsapp', read_at: null, from: '+15553333' },
  // Thread 1 extra unread
  { id: 'm6', patient_id: 'p1', patient_name: 'Alice', channel: 'sms', direction: 'inbound', body: 'Follow up from Alice', status: 'received', created_at: now, thread_key: 'p1:sms', read_at: null, from: '+15551111' },
];

describe('ThreadList renders', () => {
  it('shows ≥3 thread rows with channel icons and at least one unread badge', async () => {
    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json(messages)),
    );

    render(<CommInbox />, { wrapper });

    // Wait for threads to render
    await waitFor(() => expect(screen.getByText('Alice')).toBeInTheDocument());

    const rows = screen.getAllByTestId('thread-row');
    expect(rows.length).toBeGreaterThanOrEqual(3);

    // Channel icons present
    expect(screen.getByText(/📱/)).toBeInTheDocument();
    expect(screen.getByText(/✉️/)).toBeInTheDocument();
    expect(screen.getByText(/💬/)).toBeInTheDocument();

    // At least one unread badge (count > 0)
    const badges = document.querySelectorAll('.rounded-full.bg-blue-600');
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });
});
