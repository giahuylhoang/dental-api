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

describe('care notes saved per item', () => {
  it('PATCHes items with updated care_notes on save', async () => {
    // tp1 has 1 existing item (from treatmentPlansDb seed)
    render(<TreatmentPlanEditor patientId="p1" planId="tp1" />, { wrapper });

    // Wait for the plan to load and care_notes textarea to appear
    await waitFor(() => {
      const textareas = screen.getAllByRole('textbox', { name: /care notes/i });
      expect(textareas.length).toBeGreaterThan(0);
    });

    const notesTextarea = screen.getAllByRole('textbox', { name: /care notes/i })[0];
    fireEvent.change(notesTextarea, { target: { value: 'implant candidate' } });

    const saveBtn = screen.getByRole('button', { name: /save draft/i });
    fireEvent.click(saveBtn);

    // MSW handler updates treatmentPlansDb in-memory; verify the db was updated
    await waitFor(() => {
      const tp = treatmentPlansDb.find((p) => p.id === 'tp1');
      expect(tp).toBeDefined();
      expect(tp!.items[0].care_notes).toBe('implant candidate');
    });
  });
});
