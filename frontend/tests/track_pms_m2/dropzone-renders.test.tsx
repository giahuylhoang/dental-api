import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DocumentUploader from '../../src/features/patients/DocumentUploader';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('DocumentUploader dropzone', () => {
  it('renders a dropzone element', () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });
    expect(screen.getByTestId('dropzone')).toBeTruthy();
  });

  it('adds 3 rows to the queue when 3 files are dropped', async () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });

    const input = screen.getByTestId('file-input') as HTMLInputElement;
    const files = [
      new File(['a'], 'a.pdf', { type: 'application/pdf' }),
      new File(['b'], 'b.pdf', { type: 'application/pdf' }),
      new File(['c'], 'c.jpg', { type: 'image/jpeg' }),
    ];

    // react-dropzone reads files from the input's change event
    Object.defineProperty(input, 'files', { value: files, configurable: true });
    input.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => {
      const queue = screen.getByTestId('upload-queue');
      expect(queue.querySelectorAll('li').length).toBe(3);
    });
  });
});
