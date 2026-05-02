import { describe, it, expect } from 'vitest';
import { nextAllowed, type ApptStatus } from '../../src/features/scheduling/appt-status';

describe('appt-status state machine', () => {
  it('cannot skip from SCHEDULED to COMPLETED', () => {
    const allowed = nextAllowed('SCHEDULED');
    expect(allowed).not.toContain('COMPLETED');
  });

  it('cannot skip from SCHEDULED to IN_PROGRESS', () => {
    expect(nextAllowed('SCHEDULED')).not.toContain('IN_PROGRESS');
  });

  it('CONFIRMED → CHECKED_IN is allowed', () => {
    expect(nextAllowed('CONFIRMED')).toContain('CHECKED_IN');
  });

  it('CHECKED_IN → IN_PROGRESS is allowed', () => {
    expect(nextAllowed('CHECKED_IN')).toContain('IN_PROGRESS');
  });

  it('IN_PROGRESS → COMPLETED is allowed', () => {
    expect(nextAllowed('IN_PROGRESS')).toContain('COMPLETED');
  });

  it('COMPLETED has no transitions', () => {
    expect(nextAllowed('COMPLETED')).toHaveLength(0);
  });

  it('CANCELLED has no transitions', () => {
    expect(nextAllowed('CANCELLED')).toHaveLength(0);
  });

  it('NO_SHOW has no transitions', () => {
    expect(nextAllowed('NO_SHOW')).toHaveLength(0);
  });

  it('SCHEDULED can go to CONFIRMED', () => {
    expect(nextAllowed('SCHEDULED')).toContain('CONFIRMED');
  });

  it('SCHEDULED can go to NO_SHOW', () => {
    expect(nextAllowed('SCHEDULED')).toContain('NO_SHOW');
  });

  it('CONFIRMED can go to NO_SHOW', () => {
    expect(nextAllowed('CONFIRMED')).toContain('NO_SHOW');
  });

  it('full happy path: SCHEDULED → CONFIRMED → CHECKED_IN → IN_PROGRESS → COMPLETED', () => {
    const path: ApptStatus[] = ['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS', 'COMPLETED'];
    for (let i = 0; i < path.length - 1; i++) {
      expect(nextAllowed(path[i])).toContain(path[i + 1]);
    }
  });
});
