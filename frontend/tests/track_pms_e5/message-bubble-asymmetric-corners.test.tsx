import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThreadDetail } from '../../src/features/communications/ThreadDetail';
import type { Thread } from '../../src/features/communications/types';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

const now = new Date().toISOString();

const thread: Thread = {
  thread_key: 'p1:sms',
  patient_id: 'p1',
  patient_name: 'Alice',
  channel: 'sms',
  last_at: now,
  messages: [
    {
      id: 'out-1',
      patient_id: 'p1',
      patient_name: 'Alice',
      channel: 'sms',
      direction: 'outbound',
      body: 'Hello from clinic',
      status: 'sent',
      created_at: now,
      thread_key: 'p1:sms',
      read_at: now,
      from: 'clinic',
    },
    {
      id: 'in-1',
      patient_id: 'p1',
      patient_name: 'Alice',
      channel: 'sms',
      direction: 'inbound',
      body: 'Hello from patient',
      status: 'received',
      created_at: now,
      thread_key: 'p1:sms',
      read_at: null,
      from: '+15551234',
    },
  ],
};

describe('message-bubble-asymmetric-corners', () => {
  it('outbound bubble has rounded-br-sm class', () => {
    const { container } = render(
      <ThreadDetail thread={thread} onReply={() => {}} />,
      { wrapper },
    );

    const outbound = container.querySelector('.rounded-br-sm');
    expect(outbound).toBeTruthy();
  });

  it('inbound bubble has rounded-bl-sm class', () => {
    const { container } = render(
      <ThreadDetail thread={thread} onReply={() => {}} />,
      { wrapper },
    );

    const inbound = container.querySelector('.rounded-bl-sm');
    expect(inbound).toBeTruthy();
  });
});
