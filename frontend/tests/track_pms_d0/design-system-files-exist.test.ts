import { describe, it, expect } from 'vitest';
import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const DS = join(__dirname, '../../design_system/dental-pms.v1');

describe('D0 design-system files exist', () => {
  it('tokens.css exists', () => {
    expect(existsSync(join(DS, 'tokens.css'))).toBe(true);
  });

  it('README.md exists', () => {
    expect(existsSync(join(DS, 'README.md'))).toBe(true);
  });

  it('SKILL.md exists', () => {
    expect(existsSync(join(DS, 'SKILL.md'))).toBe(true);
  });

  it('preview/ has >=15 .html files', () => {
    const files = readdirSync(join(DS, 'preview')).filter(f => f.endsWith('.html'));
    expect(files.length).toBeGreaterThanOrEqual(15);
  });

  it('ui_kits/web/ has >=6 .tsx files', () => {
    const files = readdirSync(join(DS, 'ui_kits/web')).filter(f => f.endsWith('.tsx'));
    expect(files.length).toBeGreaterThanOrEqual(6);
  });
});
