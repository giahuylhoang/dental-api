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

const inboundSms = {
  id: 'msg-inbound-f1',
  patient_id: 'p-77',
  patient_name: 'Eve',
  channel: 'sms',
  direction: 'inbound',
  body: 'Hey there',
  status: 'received',
  from: '+15550000',
  created_at: new Date().toISOString(),
  thread_key: 'p-77:sms',
  read_at: null,
};

describe('Reply prefills channel and to', () => {
  it('opens ComposeDialog with channel=sms, to=sender, and patient_id set', async () => {
    let captured: unknown;

    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json([inboundSms])),
      http.patch('/api/v2/communications/threads/:key/read', () => HttpResponse.json({ ok: true })),
      http.post('/api/v2/communications/send', async ({ request }) => {
        captured = await request.json();
        return HttpResponse.json({ id: 'msg-out', status: 'sent' }, { status: 201 });
      }),
    );

    render(<CommInbox />, { wrapper });

    // Select thread
    await waitFor(() => expect(screen.getByText('Eve')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Eve'));

    // Click Reply
    await waitFor(() => expect(screen.getByRole('button', { name: /reply/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /reply/i }));

    // ComposeDialog opens — SMS tab should be active
    await waitFor(() => expect(screen.getByRole('heading', { name: /new message/i })).toBeInTheDocument());

    const smsTab = screen.getByRole('tab', { name: /^sms$/i });
    expect(smsTab.getAttribute('aria-selected')).toBe('true');

    expect(screen.getByDisplayValue('+15550000')).toBeInTheDocument();

    // Submit to verify patient_id is set
    fireEvent.click(screen.getByRole('button', { name: /^send$/i }));
    await waitFor(() =>
      expect(captured).toMatchObject({ channel: 'sms', to: '+15550000', patient_id: 'p-77' }),
    );
  });
});
