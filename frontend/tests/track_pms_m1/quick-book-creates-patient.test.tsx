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

describe('QuickBook creates patient and selects them', () => {
  it('click "+ Create new patient" → fill name+phone → submit → patient selected', async () => {
    let capturedBody: unknown;

    server.use(
      http.get('/api/patients', () =>
        HttpResponse.json({ items: [], total: 0, page: 1, limit: 10 }),
      ),
      http.get('/api/doctors', () => HttpResponse.json([])),
      http.get('/api/services', () => HttpResponse.json([])),
      http.post('/api/v2/clinical/patients/quick-book', async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json(
          { id: 'qb-1', first_name: 'Jane', last_name: 'Doe', phone: '555-9999' },
          { status: 201 },
        );
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

    // Type a query that returns no results to reveal "+ Create new patient"
    const searchInput = screen.getByPlaceholderText('Search patient…');
    fireEvent.change(searchInput, { target: { value: 'Jane Doe' } });

    // Wait for the "no results" state and the create button
    await waitFor(() =>
      expect(screen.getByText('+ Create new patient')).toBeInTheDocument(),
    );

    fireEvent.click(screen.getByText('+ Create new patient'));

    // QuickBookPopover should appear
    await waitFor(() =>
      expect(screen.getByText('Create new patient')).toBeInTheDocument(),
    );

    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Jane Doe' } });
    fireEvent.change(screen.getByLabelText('Phone'), { target: { value: '555-9999' } });

    // Click the Create button inside the popover (not the main dialog's disabled Create)
    const createButtons = screen.getAllByRole('button', { name: /^Create$/ });
    // The popover's Create button is the enabled one
    const popoverCreate = createButtons.find((b) => !(b as HTMLButtonElement).disabled)!;
    fireEvent.click(popoverCreate);

    // MSW should have been called
    await waitFor(() =>
      expect(capturedBody).toEqual({ name: 'Jane Doe', phone: '555-9999' }),
    );

    // Patient should now be selected (popover closes, patient name shown)
    await waitFor(() =>
      expect(screen.getByText(/Jane Doe/)).toBeInTheDocument(),
    );
  });
});
