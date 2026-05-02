import { describe, it, expect } from 'vitest';
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TreatmentPlanEditor from '../../src/features/treatment-plans/TreatmentPlanEditor';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('TreatmentPlanEditor shows tooth chart', () => {
  it('renders an SVG element for the tooth chart', async () => {
    render(<TreatmentPlanEditor patientId="p1" planId="tp1" />, { wrapper });
    // E4 moved ToothChart into the "Tooth Chart" tab — open it first
    const toothTab = await screen.findByRole('tab', { name: /tooth chart/i });
    fireEvent.pointerDown(toothTab, { pointerType: 'mouse', button: 0 });
    fireEvent.mouseDown(toothTab);
    fireEvent.click(toothTab);
    // After click, the tooth chart panel mounts and ToothChart fetches its data.
    // Wait long enough for the query to resolve and SVG to render.
    await waitFor(
      () => {
        const svg = document.querySelector('svg');
        expect(svg).not.toBeNull();
      },
      { timeout: 4000 },
    );
  });
});
