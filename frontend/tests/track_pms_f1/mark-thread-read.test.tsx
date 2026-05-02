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

const threadKey = 'p-99:sms';
const messages = [
  {
    id: 'msg-unread-1',
    patient_id: 'p-99',
    patient_name: 'Dana',
    channel: 'sms',
    direction: 'inbound',
    body: 'Unread message',
    status: 'received',
    created_at: new Date().toISOString(),
    thread_key: threadKey,
    read_at: null,
    from: '+15559999',
  },
];

describe('Mark thread read', () => {
  it('fires PATCH /api/v2/communications/threads/:thread_key/read when thread is clicked', async () => {
    let patchedUrl = '';

    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json(messages)),
      http.patch('/api/v2/communications/threads/:thread_key/read', ({ params }) => {
        patchedUrl = `/api/v2/communications/threads/${params.thread_key}/read`;
        return HttpResponse.json({ ok: true });
      }),
    );

    render(<CommInbox />, { wrapper });

    await waitFor(() => expect(screen.getByText('Dana')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Dana'));

    await waitFor(() =>
      expect(patchedUrl).toBe(`/api/v2/communications/threads/${threadKey}/read`),
    );
  });
});
