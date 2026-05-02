import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DocumentUploader from '../../src/features/patients/DocumentUploader';

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe('failed upload shows error and Retry', () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let xhrInstances: any[] = [];

  beforeEach(() => {
    xhrInstances = [];

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const MockXHR = vi.fn(function (this: any) {
      this.upload = { onprogress: null as null | ((e: ProgressEvent) => void) };
      this.onload = null;
      this.onerror = null as null | (() => void);
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

  it('shows error message and Retry button on XHR error', async () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });

    const input = screen.getByTestId('file-input') as HTMLInputElement;
    const file = new File(['data'], 'fail.pdf', { type: 'application/pdf' });
    Object.defineProperty(input, 'files', { value: [file], configurable: true });
    input.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => expect(xhrInstances.length).toBeGreaterThan(0));

    // Trigger network error
    act(() => {
      if (xhrInstances[0].onerror) xhrInstances[0].onerror();
    });

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeTruthy();
      expect(screen.getByRole('button', { name: /retry/i })).toBeTruthy();
    });
  });

  it('clicking Retry creates a new XHR', async () => {
    render(<DocumentUploader patientId="p1" />, { wrapper });

    const input = screen.getByTestId('file-input') as HTMLInputElement;
    const file = new File(['data'], 'fail2.pdf', { type: 'application/pdf' });
    Object.defineProperty(input, 'files', { value: [file], configurable: true });
    input.dispatchEvent(new Event('change', { bubbles: true }));

    await waitFor(() => expect(xhrInstances.length).toBe(1));

    act(() => {
      if (xhrInstances[0].onerror) xhrInstances[0].onerror();
    });

    await waitFor(() => screen.getByRole('button', { name: /retry/i }));

    fireEvent.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => expect(xhrInstances.length).toBe(2));
  });
});
