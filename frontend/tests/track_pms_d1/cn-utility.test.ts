import { describe, it, expect } from 'vitest';
import { cn } from '../../src/lib/utils';

describe('cn utility', () => {
  it('merges classes and last tailwind class wins', () => {
    const condition = false;
    const result = cn('a', condition && 'b', 'p-4 p-6');
    expect(result).toContain('a');
    expect(result).toContain('p-6');
    expect(result).not.toContain('p-4');
  });
});
