import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Button } from '../../src/components/ui/button';

describe('Button asChild', () => {
  it('renders as anchor when asChild with <a>', () => {
    const { container } = render(
      <Button asChild><a href="/x">Go</a></Button>
    );
    const el = container.firstChild as HTMLElement;
    expect(el.tagName.toLowerCase()).toBe('a');
    expect(el.className).toMatch(/inline-flex/);
  });
});
