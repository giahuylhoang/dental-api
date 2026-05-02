import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi } from 'vitest';
import DocumentUploader from '../../src/features/patients/DocumentUploader';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('DocumentUploader (P1 — verifies M2 react-dropzone rewrite)', () => {
  it('renders drop zone', () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });
    expect(screen.getByText(/drag & drop/i)).toBeTruthy();
  });

  it('drops a file and enqueues it in the upload list', async () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['hello'], 'test.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => {
      expect(screen.getByText('test.jpg')).toBeTruthy();
    });
    // M2 component auto-uploads — no explicit upload button, just a queue
    expect(screen.getByTestId('upload-queue')).toBeTruthy();
  });

  it('opens an XHR to the upload endpoint with multipart form data on drop', async () => {
    const opened: Array<{ method: string; url: string }> = [];
    const sentBodies: unknown[] = [];

    class MockXHR {
      upload = { onprogress: null as unknown };
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      status = 200;
      statusText = 'OK';
      open(method: string, url: string) {
        opened.push({ method, url });
      }
      setRequestHeader() {}
      send(body: unknown) {
        sentBodies.push(body);
      }
    }
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    try {
      render(<DocumentUploader patientId="p1" />, { wrapper });
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['data'], 'doc.pdf', { type: 'application/pdf' });
      fireEvent.change(input, { target: { files: [file] } });
      await waitFor(() => screen.getByText('doc.pdf'));
      await waitFor(() => {
        expect(opened.length).toBeGreaterThan(0);
      });
      expect(opened[0].method).toBe('POST');
      expect(opened[0].url).toContain('/api/v2/clinical/documents/upload');
      expect(sentBodies[0]).toBeInstanceOf(FormData);
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
