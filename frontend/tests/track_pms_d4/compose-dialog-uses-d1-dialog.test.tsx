import { describe, it, expect } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ComposeDialog } from '../../src/features/communications/ComposeDialog';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('compose-dialog-uses-d1-dialog', () => {
  it('dialog content has Radix data-state="open" attribute', async () => {
    render(<ComposeDialog onClose={() => {}} />, { wrapper });

    await waitFor(() => {
      const content = document.querySelector('[data-state="open"]');
      expect(content).not.toBeNull();
    });
  });
});
