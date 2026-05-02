import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('HSL tokens allow alpha', () => {
  it('tokens-hsl.css declares HSL triplet variables', () => {
    const css = readFileSync(
      resolve(__dirname, '../../src/design_system/tokens-hsl.css'),
      'utf-8'
    );
    // Should contain at least one HSL triplet (number deg% lightness%)
    expect(css).toMatch(/--ds-\w+:\s*\d+\s+\d+%\s+\d+%/);
  });

  it('tailwind.config.js uses hsl(var(...) / <alpha-value>) form', () => {
    const config = readFileSync(
      resolve(__dirname, '../../tailwind.config.js'),
      'utf-8'
    );
    expect(config).toMatch(/hsl\(var\(--ds-\w+\)\s*\/\s*<alpha-value>\)/);
  });
});
