import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';
import DentureCaseDrawer from '../../src/features/lab/DentureCaseDrawer';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('DentureCaseDrawer', () => {
  it('renders denture case details', async () => {
    render(
      <DentureCaseDrawer caseId="dc1" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => expect(screen.getByText(/consult/i)).toBeInTheDocument());
    expect(screen.getByText(/upper/i)).toBeInTheDocument();
  });

  it('advance button calls POST /advance', async () => {
    let called = false;
    server.use(
      http.post('/api/v2/clinical/denture-cases/dc1/advance', () => {
        called = true;
        return HttpResponse.json({ id: 'dc1', current_stage: 'prelim_imp', status: 'open' });
      }),
    );

    render(
      <DentureCaseDrawer caseId="dc1" open={true} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );
    await waitFor(() => screen.getByText(/consult/i));
    fireEvent.click(screen.getByRole('button', { name: /advance stage/i }));
    await waitFor(() => expect(called).toBe(true));
  });

  it('does not render when closed', () => {
    render(
      <DentureCaseDrawer caseId="dc1" open={false} onClose={vi.fn()} onChanged={vi.fn()} />,
      { wrapper },
    );
    expect(screen.queryByText(/Denture Case/i)).not.toBeInTheDocument();
  });
});
