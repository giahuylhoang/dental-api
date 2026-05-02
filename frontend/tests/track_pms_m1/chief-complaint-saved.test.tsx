import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import NewAppointmentDialog from '../../src/features/scheduling/NewAppointmentDialog';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('chief_complaint is sent on submit', () => {
  it('submits with chief_complaint in request body', async () => {
    let capturedBody: unknown;

    server.use(
      http.get('/api/patients', () =>
        HttpResponse.json({
          items: [{ id: 'p1', first_name: 'Alice', last_name: 'Smith' }],
          total: 1,
          page: 1,
          limit: 10,
        }),
      ),
      http.get('/api/doctors', () =>
        HttpResponse.json([{ id: 1, name: 'Dr. Johnson' }]),
      ),
      http.get('/api/services', () =>
        HttpResponse.json([{ id: 1, name: 'Cleaning' }]),
      ),
      http.post('/api/calendar/events', async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({ id: 'ev-1' }, { status: 201 });
      }),
    );

    render(
      <NewAppointmentDialog
        open={true}
        start="2026-05-10T09:00:00"
        end="2026-05-10T09:30:00"
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />,
      { wrapper },
    );

    // Search and select patient
    const searchInput = screen.getByPlaceholderText('Search patient…');
    fireEvent.change(searchInput, { target: { value: 'Alice' } });

    await waitFor(() => expect(screen.getByText('Alice Smith')).toBeInTheDocument());
    fireEvent.click(screen.getByText('Alice Smith'));

    // Select provider and service using getAllByRole
    await waitFor(() => screen.getByText('Dr. Johnson'));
    const selects = screen.getAllByRole('combobox');
    // First select is Provider, second is Service
    fireEvent.change(selects[0], { target: { value: '1' } });
    fireEvent.change(selects[1], { target: { value: '1' } });

    // Type chief complaint
    const ccTextarea = screen.getByLabelText('Pain points / Chief complaint');
    fireEvent.change(ccTextarea, { target: { value: 'tooth pain throbbing' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /Create/ }));

    await waitFor(() =>
      expect((capturedBody as Record<string, unknown>)?.chief_complaint).toBe('tooth pain throbbing'),
    );
  });
});
