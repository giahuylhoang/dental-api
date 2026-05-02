import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TreatmentPlanEditor from '../../src/features/treatment-plans/TreatmentPlanEditor';
import { treatmentPlansDb } from '../../src/mocks/treatment-plans';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe('tiptap care notes roundtrip', () => {
  it('saves care_notes text via PATCH /api/v2/treatment-plans/{id}/items', async () => {
    render(<TreatmentPlanEditor patientId="p1" planId="tp1" />, { wrapper });

    // E4 moved care notes into the "Care Notes" tab — open it first
    await waitFor(() => expect(screen.getByRole('tab', { name: /care notes/i })).toBeInTheDocument());
    {
      const t = screen.getByRole('tab', { name: /care notes/i });
      fireEvent.pointerDown(t, { pointerType: 'mouse', button: 0 });
      fireEvent.mouseDown(t);
      fireEvent.click(t);
    }

    // Wait for the plan to load and care_notes editor to appear
    await waitFor(() => {
      const editors = screen.getAllByRole('textbox', { name: /care notes/i });
      expect(editors.length).toBeGreaterThan(0);
    });

    const notesEditor = screen.getAllByRole('textbox', { name: /care notes/i })[0];
    fireEvent.change(notesEditor, { target: { value: 'needs follow-up' } });

    fireEvent.click(screen.getByRole('button', { name: /save draft/i }));

    await waitFor(() => {
      const tp = treatmentPlansDb.find((p) => p.id === 'tp1');
      expect(tp).toBeDefined();
      expect(tp!.items[0].care_notes).toBe('needs follow-up');
    });
  });
});
