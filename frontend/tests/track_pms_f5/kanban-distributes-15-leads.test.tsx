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

// 15 leads: NEW(5) CONTACTED(4) QUALIFIED(3) CONVERTED(2) LOST(1)
const DIST: [string, number][] = [
  ['NEW', 5], ['CONTACTED', 4], ['QUALIFIED', 3], ['CONVERTED', 2], ['LOST', 1],
];

const fixture = DIST.flatMap(([status, count]) =>
  Array.from({ length: count }, (_, i) => ({
    id: `fix-${status}-${i}`,
    first_name: `${status}${i}`,
    last_name: 'Fix',
    phone: null,
    email: null,
    status,
    source: null,
    notes: null,
    owner_id: null,
    clinic_id: 'default',
  })),
);

describe('kanban-distributes-15-leads', () => {
  it('each column header shows correct count', async () => {
    server.use(
      http.get('/api/v2/crm/leads', () => HttpResponse.json(fixture)),
    );

    render(<LeadKanban />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('NEW (5)')).toBeInTheDocument();
      expect(screen.getByText('CONTACTED (4)')).toBeInTheDocument();
      expect(screen.getByText('QUALIFIED (3)')).toBeInTheDocument();
      expect(screen.getByText('CONVERTED (2)')).toBeInTheDocument();
      expect(screen.getByText('LOST (1)')).toBeInTheDocument();
    });
  });
});
