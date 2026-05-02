import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DocumentUploader from '../../src/features/patients/DocumentUploader';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('progress bar updates via XHR progress events', () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let xhrInstances: any[] = [];

  beforeEach(() => {
    xhrInstances = [];

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const MockXHR = vi.fn(function (this: any) {
      this.upload = { onprogress: null as null | ((e: ProgressEvent) => void) };
      this.onload = null;
      this.onerror = null;
      this.open = vi.fn();
      this.setRequestHeader = vi.fn();
      this.send = vi.fn();
      xhrInstances.push(this);
    });

    vi.stubGlobal('XMLHttpRequest', MockXHR);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('progress bar width reflects loaded/total', async () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });

    const input = screen.getByTestId('file-input') as HTMLInputElement;
    const file = new File(['hello'], 'test.pdf', { type: 'application/pdf' });
    Object.defineProperty(input, 'files', { value: [file], configurable: true });
    input.dispatchEvent(new Event('change', { bubbles: true }));

    // Wait for XHR to be created and queue row to appear
    await waitFor(() => expect(xhrInstances.length).toBeGreaterThan(0));

    const xhr = xhrInstances[0];

    // Fire progress event: 50 of 100 bytes
    act(() => {
      if (xhr.upload.onprogress) {
        xhr.upload.onprogress({ lengthComputable: true, loaded: 50, total: 100 } as ProgressEvent);
      }
    });

    await waitFor(() => {
      const bar = document.querySelector('[data-testid^="progress-bar-"]') as HTMLElement | null;
      expect(bar).not.toBeNull();
      expect(bar!.style.width).toBe('50%');
    });
  });
});
