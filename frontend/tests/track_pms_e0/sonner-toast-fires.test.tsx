import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { toast } from 'sonner';
import { Toaster } from '../../src/components/ui/sonner';

describe('Sonner toast fires', () => {
  it('toast text appears in DOM', async () => {
    render(<Toaster />);
    toast('hi');
    // Sonner renders toasts into the Toaster portal
    const toastEl = await screen.findByText('hi');
    expect(toastEl).toBeTruthy();
  });
});
