import { describe, it, expect } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import CommInbox from '../../src/features/communications/CommInbox';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('comms-resizable-panes', () => {
  it('renders resizable panel group (data-panel-group or data-group attribute)', async () => {
    server.use(
      http.get('/api/v2/communications', () => HttpResponse.json([])),
    );

    const { container } = render(<CommInbox />, { wrapper });

    await waitFor(() => {
      // react-resizable-panels v4 uses data-group; v2/v3 uses data-panel-group
      const panelGroup =
        container.querySelector('[data-panel-group]') ??
        container.querySelector('[data-group]');
      expect(panelGroup).toBeTruthy();
    });
  });
});
