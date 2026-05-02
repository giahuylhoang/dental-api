import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import CommandPalette from '../../src/features/search/CommandPalette';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  localStorage.clear();
  mockNavigate.mockReset();
});

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('palette-enter-navigates', () => {
  it('navigates to /patients/<id> on Enter after ArrowDown', async () => {
    server.use(
      http.get('/api/patients', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q') ?? '';
        if (q.toLowerCase().includes('ali')) {
          return HttpResponse.json({
            items: [{ id: 'alice-1', first_name: 'Alice', last_name: 'Wonder', phone: '555-0001' }],
            total: 1,
          });
        }
        return HttpResponse.json({ items: [], total: 0 });
      }),
    );

    render(<CommandPalette />, { wrapper });
    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    const input = screen.getByPlaceholderText(/search patients/i);
    fireEvent.change(input, { target: { value: 'ali' } });

    await waitFor(() => expect(screen.getByText('Alice Wonder')).toBeInTheDocument(), { timeout: 1000 });

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/patients/alice-1'));
  });
});
