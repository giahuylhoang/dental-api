import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import AppointmentDrawer from '../../src/features/scheduling/AppointmentDrawer';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('AppointmentDrawer uses Sheet', () => {
  it('renders as a Sheet (right-side slide) with data-state="open"', () => {
    server.use(
      http.get('/api/appointments/:id', () =>
        HttpResponse.json({
          id: 'appt-1',
          patient_id: 'p-1',
          doctor_id: 1,
          service_id: 1,
          start_time: '2026-05-10T09:00:00',
          end_time: '2026-05-10T09:30:00',
          status: 'SCHEDULED',
          doctor_name: 'Dr. Smith',
          service_name: 'Cleaning',
        }),
      ),
      http.get('/api/patients/:id', () =>
        HttpResponse.json({ id: 'p-1', first_name: 'Alice', last_name: 'Smith' }),
      ),
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

    // Sheet (Radix Dialog) sets data-state="open"
    const sheetContent = document.querySelector('[data-state="open"]');
    expect(sheetContent).not.toBeNull();
  });

  it('renders Appointment Details heading', () => {
    server.use(
      http.get('/api/appointments/:id', () =>
        HttpResponse.json({
          id: 'appt-1',
          patient_id: 'p-1',
          doctor_id: 1,
          service_id: 1,
          start_time: '2026-05-10T09:00:00',
          end_time: '2026-05-10T09:30:00',
          status: 'SCHEDULED',
        }),
      ),
      http.get('/api/patients/:id', () =>
        HttpResponse.json({ id: 'p-1', first_name: 'Alice', last_name: 'Smith' }),
      ),
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

    expect(screen.getByText('Appointment Details')).toBeInTheDocument();
  });
});
