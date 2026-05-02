import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import LeadKanban from '../../src/features/crm/LeadKanban';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('kanban-shows-skeletons-while-loading', () => {
  it('shows ≥5 skeleton cards while loading, then removes them', async () => {
    let resolve!: (value: Response) => void;
    const pending = new Promise<Response>((r) => { resolve = r; });

    server.use(
      http.get('/api/v2/crm/leads', () => pending as unknown as ReturnType<typeof HttpResponse.json>),
    );

    render(<LeadKanban />, { wrapper });

    // Skeletons visible immediately
    expect(screen.getAllByTestId('lead-skeleton').length).toBeGreaterThanOrEqual(5);

    // Resolve with empty data
    resolve(HttpResponse.json([]) as unknown as Response);

    // Skeletons gone once data arrives
    await waitFor(() =>
      expect(screen.queryAllByTestId('lead-skeleton')).toHaveLength(0),
    );
  });
});
