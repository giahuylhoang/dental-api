import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from '../../src/features/reporting/Dashboard';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('dashboard-uses-ui-button', () => {
  it('renders at least one element with the D1 button cva root class', () => {
    render(<Dashboard />, { wrapper });
    // D1 Button cva root: 'inline-flex items-center justify-center'
    const buttons = document.querySelectorAll('.inline-flex.items-center.justify-center');
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });
});
