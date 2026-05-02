import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Dialog, DialogTrigger, DialogContent, DialogTitle } from '../../src/components/ui/dialog';

describe('Dialog opens and closes', () => {
  it('shows content on trigger click and hides on Escape', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Test dialog</DialogTitle>
          <p>Dialog body</p>
        </DialogContent>
      </Dialog>
    );

    expect(screen.queryByText('Dialog body')).toBeNull();
    fireEvent.click(screen.getByText('Open'));
    expect(screen.getByText('Dialog body')).toBeInTheDocument();

    fireEvent.keyDown(document.activeElement || document.body, { key: 'Escape' });
    // After Escape the content should be removed from DOM
    expect(screen.queryByText('Dialog body')).toBeNull();
  });
});
