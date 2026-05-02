import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
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

describe('lead-kanban-uses-skeleton-from-d1', () => {
  it('skeletons have the D1 animate-pulse class from <Skeleton>', () => {
    let resolve!: (value: Response) => void;
    const pending = new Promise<Response>((r) => { resolve = r; });

    server.use(
      http.get('/api/v2/crm/leads', () => pending as unknown as ReturnType<typeof HttpResponse.json>),
    );

    render(<LeadKanban />, { wrapper });

    const skeletons = screen.getAllByTestId('lead-skeleton');
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
    // D1 Skeleton always has animate-pulse
    skeletons.forEach((el) => expect(el.className).toMatch(/animate-pulse/));

    resolve(HttpResponse.json([]) as unknown as Response);
  });
});
