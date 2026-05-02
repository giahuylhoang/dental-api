import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import { PatientSearchInput } from '../../src/features/patients/PatientSearchInput';

const alice = { id: 'p1', first_name: 'Alice', last_name: 'Smith', phone: '555-0101', email: 'alice@example.com', date_of_birth: '1975-03-15', status: 'active', clinic_id: 'default' };

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('PatientSearchInput onSelect fires', () => {
  it('calls onSelect with full patient object when result clicked', async () => {
    server.use(
      http.get('/api/patients', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q') ?? '';
        const items = q.toLowerCase().includes('ali') ? [alice] : [];
        return HttpResponse.json({ items, total: items.length, page: 1, limit: 10 });
      }),
    );

    const onSelect = vi.fn();
    render(<PatientSearchInput onSelect={onSelect} />, { wrapper });

    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'ali' } });
    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument());

    fireEvent.mouseDown(screen.getByText('Alice Smith'));
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({
      id: 'p1',
      first_name: 'Alice',
      last_name: 'Smith',
    }));
  });
});
