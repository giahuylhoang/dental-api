import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import DocumentUploader from '../../src/features/patients/DocumentUploader';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('DocumentUploader', () => {
  it('renders drop zone', async () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });
    expect(screen.getByText(/drag & drop/i)).toBeTruthy();
  });

  it('accepts a file and enables upload button', async () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['hello'], 'test.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => {
      expect(screen.getByText('test.jpg')).toBeTruthy();
    });
    const uploadBtn = screen.getByRole('button', { name: /upload/i });
    expect(uploadBtn).not.toBeDisabled();
  });

  it('posts multipart on upload', async () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['data'], 'doc.pdf', { type: 'application/pdf' });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => screen.getByText('doc.pdf'));
    fireEvent.click(screen.getByRole('button', { name: /upload/i }));
    await waitFor(() => {
      expect(screen.getByText(/uploaded successfully/i)).toBeTruthy();
    });
  });
});
