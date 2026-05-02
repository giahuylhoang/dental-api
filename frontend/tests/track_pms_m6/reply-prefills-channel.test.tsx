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
  id: 'msg-inbound-1',
  patient_id: 'p-42',
  patient_name: 'Bob',
  channel: 'sms',
  direction: 'inbound',
  body: 'Hi there',
  status: 'received',
  from: '+15550101010',
  created_at: new Date().toISOString(),
};

describe('Reply prefills channel and to', () => {
  it('clicking Reply on an inbound SMS opens compose with channel=sms and to=sender', async () => {
    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json([inboundSms])),
    );

    render(<CommInbox />, { wrapper });

    // Select the thread
    await waitFor(() => expect(screen.getByText('Bob')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Bob'));

    // Click Reply on the inbound message
    await waitFor(() => expect(screen.getByRole('button', { name: /reply/i })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /reply/i }));

    // Compose dialog should open with SMS selected and to prefilled
    await waitFor(() => expect(screen.getByRole('button', { name: /whatsapp/i })).toBeInTheDocument());

    const smsBtn = screen.getByRole('button', { name: /^sms$/i });
    expect(smsBtn).toHaveAttribute('aria-pressed', 'true');

    const toInput = screen.getByDisplayValue('+15550101010');
    expect(toInput).toBeInTheDocument();
  });
});
