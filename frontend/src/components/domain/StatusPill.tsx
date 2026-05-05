interface StatusPillProps {
  status: string;
  label?: string;
}

const STATUS_MAP: Record<string, { bg: string; fg: string; label: string }> = {
  confirmed: { bg: '#E8F5EE', fg: '#2A7D4F', label: 'Confirmed' },
  pending: { bg: '#FDF3E5', fg: '#B45309', label: 'Pending' },
  no_show: { bg: '#F8E5E8', fg: '#9B2335', label: 'No-show' },
  completed: { bg: '#F5F2EC', fg: '#4A5568', label: 'Completed' },
  active: { bg: '#E8F5EE', fg: '#2A7D4F', label: 'Active' },
  recall: { bg: '#FDF3E5', fg: '#B45309', label: 'Recall' },
  plan: { bg: '#F5F2EC', fg: '#4A5568', label: 'Plan' },
  inactive: { bg: '#F5F2EC', fg: '#8A9BB0', label: 'Inactive' },
  paid: { bg: '#E8F5EE', fg: '#2A7D4F', label: 'Paid' },
  partial: { bg: '#FDF3E5', fg: '#B45309', label: 'Partial' },
  outstanding: { bg: '#F8E5E8', fg: '#9B2335', label: 'Outstanding' },
  sent: { bg: '#FDF3E5', fg: '#B45309', label: 'Sent' },
  progress: { bg: '#D9EAF5', fg: '#2E6494', label: 'In progress' },
  returned: { bg: '#E8F5EE', fg: '#2A7D4F', label: 'Returned' },
  new: { bg: '#D9EAF5', fg: '#2E6494', label: 'New' },
  contacted: { bg: '#FDF3E5', fg: '#B45309', label: 'Contacted' },
  qualified: { bg: '#E8F5EE', fg: '#2A7D4F', label: 'Qualified' },
  converted: { bg: '#D9EAF5', fg: '#2E6494', label: 'Converted' },
  lost: { bg: '#F5F2EC', fg: '#8A9BB0', label: 'Lost' },
};

export function StatusPill({ status, label }: StatusPillProps) {
  const tone = STATUS_MAP[status] || { bg: '#F5F2EC', fg: '#4A5568', label: status };
  return (
    <span style={{
      fontSize: '0.66rem', fontWeight: 600, padding: '3px 10px', borderRadius: 4,
      letterSpacing: '0.06em', textTransform: 'uppercase',
      background: tone.bg, color: tone.fg,
    }}>{label || tone.label}</span>
  );
}
