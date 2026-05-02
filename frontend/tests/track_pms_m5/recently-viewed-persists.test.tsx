import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { markVisited } from '../../src/features/search/recentlyViewed';
import CommandPalette from '../../src/features/search/CommandPalette';

beforeEach(() => {
  localStorage.clear();
});

describe('Recently viewed persists', () => {
  it('shows recently visited item at top of palette', () => {
    markVisited('patient', 'p-123', 'Alice Johnson');

    render(
      <MemoryRouter>
        <CommandPalette />
      </MemoryRouter>,
    );

    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
  });

  it('persists across remounts', () => {
    markVisited('patient', 'p-456', 'Bob Smith');

    const { unmount } = render(
      <MemoryRouter>
        <CommandPalette />
      </MemoryRouter>,
    );
    unmount();

    render(
      <MemoryRouter>
        <CommandPalette />
      </MemoryRouter>,
    );

    fireEvent.keyDown(window, { key: 'k', metaKey: true });
    expect(screen.getByText('Bob Smith')).toBeInTheDocument();
  });
});
