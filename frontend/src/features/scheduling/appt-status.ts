export const APPT_STATUSES = [
  'SCHEDULED',
  'CONFIRMED',
  'CHECKED_IN',
  'IN_PROGRESS',
  'COMPLETED',
  'NO_SHOW',
  'CANCELLED',
] as const;

export type ApptStatus = (typeof APPT_STATUSES)[number];

const TRANSITIONS: Record<ApptStatus, ApptStatus[]> = {
  SCHEDULED: ['CONFIRMED', 'NO_SHOW', 'CANCELLED'],
  CONFIRMED: ['CHECKED_IN', 'NO_SHOW', 'CANCELLED'],
  CHECKED_IN: ['IN_PROGRESS', 'CANCELLED'],
  IN_PROGRESS: ['COMPLETED', 'CANCELLED'],
  COMPLETED: [],
  NO_SHOW: [],
  CANCELLED: [],
};

export function nextAllowed(current: ApptStatus): ApptStatus[] {
  return TRANSITIONS[current] ?? [];
}

const COLORS: Record<ApptStatus, string> = {
  SCHEDULED: 'bg-blue-100 text-blue-800',
  CONFIRMED: 'bg-indigo-100 text-indigo-800',
  CHECKED_IN: 'bg-yellow-100 text-yellow-800',
  IN_PROGRESS: 'bg-orange-100 text-orange-800',
  COMPLETED: 'bg-green-100 text-green-800',
  NO_SHOW: 'bg-red-100 text-red-800',
  CANCELLED: 'bg-zinc-100 text-zinc-500',
};

export function statusColor(s: ApptStatus): string {
  return COLORS[s];
}

const LABELS: Record<ApptStatus, string> = {
  SCHEDULED: 'Scheduled',
  CONFIRMED: 'Confirmed',
  CHECKED_IN: 'Checked In',
  IN_PROGRESS: 'In Progress',
  COMPLETED: 'Completed',
  NO_SHOW: 'No Show',
  CANCELLED: 'Cancelled',
};

export function statusLabel(s: ApptStatus): string {
  return LABELS[s];
}
