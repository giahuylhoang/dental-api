import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render } from '@testing-library/react';
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

describe('sidebar-collapses-at-narrow-viewport', () => {
  const originalWidth = window.innerWidth;

  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 800 });
    window.dispatchEvent(new Event('resize'));
  });

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: originalWidth });
    window.dispatchEvent(new Event('resize'));
  });

  it('sidebar is collapsed (icon-only) at 800px viewport', () => {
    const { container } = render(<AppShell><div>content</div></AppShell>, { wrapper });
    const sidebar = container.querySelector('[data-collapsed="true"]');
    expect(sidebar).not.toBeNull();
  });
});
