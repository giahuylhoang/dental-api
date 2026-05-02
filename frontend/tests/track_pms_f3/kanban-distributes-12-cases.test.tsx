import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';
import LabCaseKanban from '../../src/features/lab/LabCaseKanban';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

const STATUSES = ['draft', 'sent', 'in_progress', 'returned', 'remake'] as const;

// 12 cases, at least 1 per column (2 per column + 2 extra)
const seed = Array.from({ length: 12 }, (_, i) => ({
  id: `lc-k${i}`,
  case_number: `LC-2026-${String(i + 1).padStart(4, '0')}`,
  denture_case_id: 'dc1',
  vendor_id: 'v1',
  status: STATUSES[i % STATUSES.length],
  sent_at: null,
  due_back_at: null,
  lab_fee: null,
  remake_of_id: null,
  remake_reason: null,
  treatment_plan_id: null,
}));

describe('kanban-distributes-12-cases', () => {
  it('each column header shows count > 0', async () => {
    server.use(
      http.get('/api/v2/lab/cases', () => HttpResponse.json(seed)),
    );

    render(<LabCaseKanban />, { wrapper });

    // Each column header shows "Label (N)" where N > 0
    await waitFor(() => {
      const headers = screen.getAllByRole('heading', { level: 3 });
      expect(headers.length).toBe(5);
      for (const h of headers) {
        const match = h.textContent?.match(/\((\d+)\)/);
        expect(match).not.toBeNull();
        expect(Number(match![1])).toBeGreaterThan(0);
      }
    });
  });
});
