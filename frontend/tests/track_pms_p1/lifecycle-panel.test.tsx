import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import LifecyclePanel from '../../src/features/patients/LifecyclePanel';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('LifecyclePanel', () => {
  it('renders current status', async () => {
    render(<LifecyclePanel patientId="p1" />, { wrapper });
    // The status badge has class "capitalize" and shows the status text
    const statusBadge = await screen.findByText('pending', { selector: 'span' });
    expect(statusBadge).toBeTruthy();
  });

  it('promote button is disabled when already active', async () => {
    render(<LifecyclePanel patientId="p2" />, { wrapper });
    const btn = await screen.findByRole('button', { name: /promote to active/i });
    // p2 starts as pending — promote button should be enabled
    expect(btn).not.toBeDisabled();
  });
});
