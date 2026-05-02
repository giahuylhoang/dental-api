import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Skeleton } from '../../src/components/ui/skeleton';

describe('Skeleton', () => {
  it('has animate-pulse class', () => {
    const { container } = render(<Skeleton className="h-4 w-20" />);
    expect((container.firstChild as HTMLElement).className).toMatch(/animate-pulse/);
  });
});
