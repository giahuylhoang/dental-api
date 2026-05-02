import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { server } from '../../src/mocks/server';
import { http, HttpResponse } from 'msw';
import AppointmentDrawer from '../../src/features/scheduling/AppointmentDrawer';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AppointmentDrawer', () => {
  it('renders appointment details', async () => {
    render(
      <AppointmentDrawer
        appointmentId="appt-1"
        open={true}
        onClose={vi.fn()}
        onChanged={vi.fn()}
      />,
      { wrapper },
    );
    await waitFor(() => expect(screen.getByText(/Alice Smith/i)).toBeInTheDocument());
    expect(screen.getByText(/Dr\. Johnson/i)).toBeInTheDocument();
    expect(screen.getByText(/Cleaning/i)).toBeInTheDocument();
  });

  it('"Confirm" button is enabled when status is SCHEDULED', async () => {
    render(
      <AppointmentDrawer
        appointmentId="appt-1"
        open={true}
        onClose={vi.fn()}
        onChanged={vi.fn()}
      />,
      { wrapper },
    );
    await waitFor(() => screen.getByText(/Alice Smith/i));
    const btn = screen.getByRole('button', { name: /confirm/i });
    expect(btn).not.toBeDisabled();
  });

  it('"Confirm" button is disabled when status is CONFIRMED', async () => {
    render(
      <AppointmentDrawer
        appointmentId="appt-2"
        open={true}
        onClose={vi.fn()}
        onChanged={vi.fn()}
      />,
      { wrapper },
    );
    await waitFor(() => screen.getByText(/Bob Jones/i));
    const btn = screen.getByRole('button', { name: /confirm/i });
    expect(btn).toBeDisabled();
  });

  it('clicking "Confirm" calls PUT /api/appointments/:id/status with CONFIRMED', async () => {
    let capturedBody: unknown;
    server.use(
      http.put('/api/appointments/appt-1/status', async ({ request }) => {
        capturedBody = await request.json();
        return HttpResponse.json({ id: 'appt-1', status: 'CONFIRMED' });
      }),
    );

    render(
      <AppointmentDrawer
        appointmentId="appt-1"
        open={true}
        onClose={vi.fn()}
        onChanged={vi.fn()}
      />,
      { wrapper },
    );
    await waitFor(() => screen.getByText(/Alice Smith/i));
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
    await waitFor(() => expect(capturedBody).toEqual({ status: 'CONFIRMED' }));
  });

  it('does not render when closed', () => {
    render(
      <AppointmentDrawer
        appointmentId="appt-1"
        open={false}
        onClose={vi.fn()}
        onChanged={vi.fn()}
      />,
      { wrapper },
    );
    expect(screen.queryByText(/Appointment Details/i)).not.toBeInTheDocument();
  });
});
