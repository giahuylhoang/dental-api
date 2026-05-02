import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const readme = readFileSync(
  join(__dirname, '../../design_system/dental-pms.v1/README.md'),
  'utf-8'
);

describe('README.md has required headings', () => {
  it('contains "Design philosophy"', () => {
    expect(readme).toContain('Design philosophy');
  });

  it('contains "Color story"', () => {
    expect(readme).toContain('Color story');
  });

  it('contains "Component principles"', () => {
    expect(readme).toContain('Component principles');
  });
});
