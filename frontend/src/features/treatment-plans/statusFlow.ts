export interface StatusAction {
  label: string;
  endpoint: string; // relative path segment, e.g. "present"
  variant?: 'default' | 'green' | 'red';
}

const FLOW: Record<string, StatusAction[]> = {
  draft: [{ label: 'Present', endpoint: 'present' }],
  presented: [
    { label: 'Accept', endpoint: 'accept', variant: 'green' },
    { label: 'Decline', endpoint: 'decline', variant: 'red' },
  ],
  accepted: [{ label: 'Mark in progress', endpoint: 'in-progress' }],
  in_progress: [{ label: 'Complete', endpoint: 'complete', variant: 'green' }],
};

export function nextActions(status: string): StatusAction[] {
  return FLOW[status] ?? [];
}
