import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { server } from '../../src/mocks/server';
import Scheduler from '../../src/features/scheduling/Scheduler';

vi.mock('@fullcalendar/react', () => ({
  default: vi.fn(({ select, eventClick }) => {
    if (typeof window !== 'undefined') {
      (window as unknown as Record<string, unknown>)['__fcSelect'] = select;
      (window as unknown as Record<string, unknown>)['__fcEventClick'] = eventClick;
    }
    return <div className="fc" data-testid="fullcalendar" />;
  }),
}));
vi.mock('@fullcalendar/timegrid', () => ({ default: {} }));
vi.mock('@fullcalendar/daygrid', () => ({ default: {} }));
vi.mock('@fullcalendar/interaction', () => ({ default: {} }));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Scheduler redesign (E1)', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/calendar/events', () => HttpResponse.json([])),
      http.get('/api/doctors', () => HttpResponse.json([{ id: 1, name: 'Dr. Smith' }])),
      http.get('/api/services', () => HttpResponse.json([{ id: 1, name: 'Cleaning' }])),
    );
  });

  it('renders PageHeader with title "Schedule"', () => {
    render(<Scheduler />, { wrapper });
    expect(screen.getByText('Schedule')).toBeInTheDocument();
  });

  it('renders provider filter select', () => {
    render(<Scheduler />, { wrapper });
    // The provider filter trigger should be present
    expect(screen.getByTestId('provider-filter')).toBeInTheDocument();
  });

  it('renders view toggle tabs: Day, Week, Month', () => {
    render(<Scheduler />, { wrapper });
    expect(screen.getByRole('tab', { name: 'Day' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Week' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Month' })).toBeInTheDocument();
  });

  it('renders "+ New appointment" button', () => {
    render(<Scheduler />, { wrapper });
    expect(screen.getByRole('button', { name: /new appointment/i })).toBeInTheDocument();
  });

  it('renders FullCalendar .fc root', () => {
    render(<Scheduler />, { wrapper });
    expect(document.querySelector('.fc')).not.toBeNull();
  });
});
