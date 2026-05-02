import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const previewDir = join(__dirname, '../../design_system/dental-pms.v1/preview');

describe('preview pages import tokens', () => {
  const htmlFiles = readdirSync(previewDir).filter(f => f.endsWith('.html'));

  for (const file of htmlFiles) {
    it(`${file} references tokens.css`, () => {
      const content = readFileSync(join(previewDir, file), 'utf-8');
      expect(content).toMatch(/tokens\.css/);
    });
  }
});
