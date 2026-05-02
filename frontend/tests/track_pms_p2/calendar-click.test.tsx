import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import Calendar from '../../src/features/scheduling/Calendar';

// Seed one appointment in the current week so it shows up
const TODAY = new Date();
const weekStart = new Date(TODAY);
weekStart.setDate(TODAY.getDate() - TODAY.getDay());
const apptDate = new Date(weekStart);
apptDate.setDate(weekStart.getDate() + 1); // Tuesday
const apptDateStr = apptDate.toISOString().slice(0, 10);

const mockAppt = {
  id: 'cal-appt-1',
  patient_id: 'p1',
  doctor_id: 1,
  service_id: 1,
  start_time: `${apptDateStr}T09:00:00`,
  end_time: `${apptDateStr}T10:00:00`,
  status: 'SCHEDULED',
};

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Calendar click opens drawer', () => {
  it('clicking an appointment block opens the AppointmentDrawer', async () => {
    server.use(
      http.get('/api/appointments', () => HttpResponse.json([mockAppt])),
      http.get('/api/appointments/cal-appt-1', () =>
        HttpResponse.json({
          ...mockAppt,
          patient_name: 'Alice Smith',
          doctor_name: 'Dr. Johnson',
          service_name: 'Cleaning',
        }),
      ),
    );

    render(<Calendar />, { wrapper });

    // Wait for the appointment block to appear (shows patient_id prefix)
    await waitFor(() => screen.getByText(/p1/i));

    // Click the appointment block
    fireEvent.click(screen.getByText(/p1/i));

    // Drawer should open and load appointment details
    await waitFor(() =>
      expect(screen.getByText(/Appointment Details/i)).toBeInTheDocument(),
    );
    await waitFor(() =>
      expect(screen.getByText(/Alice Smith/i)).toBeInTheDocument(),
    );
  });
});
