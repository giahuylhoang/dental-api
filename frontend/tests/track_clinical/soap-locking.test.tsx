import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SoapEditor from '../../src/features/clinical/notes/SoapEditor';

function renderEditor(initialNote?: Parameters<typeof SoapEditor>[0]['initialNote']) {
  const qc = new QueryClient();
  const onSave = vi.fn();
  const utils = render(
    <QueryClientProvider client={qc}>
      <SoapEditor patientId="p1" initialNote={initialNote} onSave={onSave} />
    </QueryClientProvider>,
  );
  return { ...utils, onSave };
}

describe('SoapEditor locking', () => {
  it('renders four SOAP sections', () => {
    renderEditor();
    expect(screen.getByLabelText('Subjective')).toBeInTheDocument();
    expect(screen.getByLabelText('Objective')).toBeInTheDocument();
    expect(screen.getByLabelText('Assessment')).toBeInTheDocument();
    expect(screen.getByLabelText('Plan')).toBeInTheDocument();
  });

  it('fields are editable when unlocked', () => {
    renderEditor();
    const subj = screen.getByLabelText('Subjective') as HTMLTextAreaElement;
    expect(subj.disabled).toBe(false);
  });

  it('locked note disables all fields', () => {
    renderEditor({
      patient_id: 'p1',
      soap_subjective: 'S',
      soap_objective: 'O',
      soap_assessment: 'A',
      soap_plan: 'P',
      locked_at: '2026-05-01T10:00:00Z',
    });
    const fields = ['Subjective', 'Objective', 'Assessment', 'Plan'];
    for (const f of fields) {
      expect((screen.getByLabelText(f) as HTMLTextAreaElement).disabled).toBe(true);
    }
  });

  it('locked note shows Amend button', () => {
    renderEditor({
      patient_id: 'p1',
      soap_subjective: 'S',
      soap_objective: 'O',
      soap_assessment: 'A',
      soap_plan: 'P',
      locked_at: '2026-05-01T10:00:00Z',
    });
    expect(screen.getByRole('button', { name: 'Amend' })).toBeInTheDocument();
  });

  it('Amend opens fresh editor with supersedes_id', async () => {
    renderEditor({
      id: 'note-1',
      patient_id: 'p1',
      soap_subjective: 'S',
      soap_objective: 'O',
      soap_assessment: 'A',
      soap_plan: 'P',
      locked_at: '2026-05-01T10:00:00Z',
    });
    fireEvent.click(screen.getByRole('button', { name: 'Amend' }));
    await waitFor(() =>
      expect(screen.getByText(/Amending note/)).toBeInTheDocument(),
    );
    // Fields should now be editable (amendment editor)
    const subj = screen.getByLabelText('Subjective') as HTMLTextAreaElement;
    expect(subj.disabled).toBe(false);
    expect(subj.value).toBe('');
  });

  it('Lock button requires confirmation', () => {
    renderEditor();
    const lockBtn = screen.getByRole('button', { name: 'Lock' });
    fireEvent.click(lockBtn);
    expect(screen.getByRole('button', { name: 'Confirm Lock?' })).toBeInTheDocument();
  });

  it('confirming lock disables fields', async () => {
    renderEditor();
    fireEvent.click(screen.getByRole('button', { name: 'Lock' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Lock?' }));
    await waitFor(() => {
      const subj = screen.getByLabelText('Subjective') as HTMLTextAreaElement;
      expect(subj.disabled).toBe(true);
    });
  });
});
