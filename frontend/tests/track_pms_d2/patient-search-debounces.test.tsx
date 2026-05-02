import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import { PatientSearchInput } from '../../src/features/patients/PatientSearchInput';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('PatientSearchInput debounces', () => {
  it('fires GET exactly once after typing quickly', async () => {
    vi.useFakeTimers();
    let callCount = 0;
    let lastQ = '';

    server.use(
      http.get('/api/patients', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q') ?? '';
        callCount++;
        lastQ = q;
        return HttpResponse.json({ items: [], total: 0, page: 1, limit: 10 });
      }),
    );

    render(<PatientSearchInput onSelect={vi.fn()} />, { wrapper });
    const input = screen.getByRole('textbox');

    // Type quickly within 100ms each
    for (const val of ['a', 'al', 'ali', 'alic', 'alice']) {
      fireEvent.change(input, { target: { value: val } });
    }

    // Advance past debounce
    await vi.advanceTimersByTimeAsync(250);

    expect(callCount).toBe(1);
    expect(lastQ).toBe('alice');

    vi.useRealTimers();
  });
});
