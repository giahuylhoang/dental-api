import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import AppShell from '../../src/features/shell/AppShell';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('sidebar-becomes-sheet-below-768', () => {
  const originalWidth = window.innerWidth;

  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 600 });
    window.dispatchEvent(new Event('resize'));
  });

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: originalWidth });
    window.dispatchEvent(new Event('resize'));
  });

  it('shows hamburger button at 600px and opens sheet on click', () => {
    render(<AppShell><div>content</div></AppShell>, { wrapper });
    const hamburger = screen.getByTestId('hamburger');
    expect(hamburger).toBeInTheDocument();
    fireEvent.click(hamburger);
    // Sheet is open — sidebar nav items should be visible
    expect(screen.getByText('Patients')).toBeInTheDocument();
  });
});
