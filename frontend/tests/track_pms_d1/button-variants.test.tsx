import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Button } from '../../src/components/ui/button';

describe('Button variants', () => {
  it('renders destructive variant with sm size', () => {
    const { container } = render(<Button variant="destructive" size="sm">x</Button>);
    const btn = container.firstChild as HTMLElement;
    expect(btn.className).toMatch(/destructive/);
    expect(btn.className).toMatch(/h-9/);
  });
});
