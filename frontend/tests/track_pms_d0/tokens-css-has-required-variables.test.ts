import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const css = readFileSync(
  join(__dirname, '../../design_system/dental-pms.v1/tokens.css'),
  'utf-8'
);

describe('tokens.css has required variables', () => {
  const required = [
    '--ds-clinical-500',
    '--ds-action-500',
    '--color-text-primary',
    '--color-action',
    '--font-display',
    '--text-base',
    '--space-4',
    '--radius-md',
    '--shadow-md',
    '--duration-base',
  ];

  for (const token of required) {
    it(`contains ${token}`, () => {
      expect(css).toContain(token);
    });
  }
});
