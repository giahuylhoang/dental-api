import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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

// Helper: activate a Radix tab via keyboard (Radix responds to Enter/Space)
function activateTab(tab: HTMLElement) {
  tab.focus();
  fireEvent.keyDown(tab, { key: 'Enter' });
}

describe('Scheduler view toggle tabs', () => {
  let viewChangeSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    viewChangeSpy = vi.fn();
    (window as unknown as Record<string, unknown>)['__onViewChange'] = viewChangeSpy;
    server.use(
      http.get('/api/calendar/events', () => HttpResponse.json([])),
      http.get('/api/doctors', () => HttpResponse.json([])),
      http.get('/api/services', () => HttpResponse.json([])),
    );
  });

  it('activating Day tab calls changeView("timeGridDay")', () => {
    render(<Scheduler />, { wrapper });
    activateTab(screen.getByRole('tab', { name: 'Day' }));
    expect(viewChangeSpy).toHaveBeenCalledWith('timeGridDay');
  });

  it('activating Month tab calls changeView("dayGridMonth")', () => {
    render(<Scheduler />, { wrapper });
    activateTab(screen.getByRole('tab', { name: 'Month' }));
    expect(viewChangeSpy).toHaveBeenCalledWith('dayGridMonth');
  });

  it('activating Week tab after switching away calls changeView("timeGridWeek")', () => {
    render(<Scheduler />, { wrapper });
    // Switch to Day first, then back to Week
    activateTab(screen.getByRole('tab', { name: 'Day' }));
    viewChangeSpy.mockClear();
    activateTab(screen.getByRole('tab', { name: 'Week' }));
    expect(viewChangeSpy).toHaveBeenCalledWith('timeGridWeek');
  });
});
