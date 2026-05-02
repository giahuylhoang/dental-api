import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Badge } from '../../src/components/ui/badge';

describe('Badge variants', () => {
  it('success variant has green classes', () => {
    const { container } = render(<Badge variant="success">OK</Badge>);
    expect((container.firstChild as HTMLElement).className).toMatch(/green/);
  });

  it('warning variant has yellow classes', () => {
    const { container } = render(<Badge variant="warning">Warn</Badge>);
    expect((container.firstChild as HTMLElement).className).toMatch(/yellow/);
  });
});
