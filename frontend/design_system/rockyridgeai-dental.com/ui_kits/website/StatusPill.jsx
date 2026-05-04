// StatusPill — single source of truth for all status enums
const StatusPill = ({ kind, value }) => {
  const TONES = {
    success: { bg: '#E8F5EE', color: '#2A7D4F' },
    warn:    { bg: '#FDF3E5', color: '#B45309' },
    danger:  { bg: '#F8E5E8', color: '#9B2335' },
    info:    { bg: '#D9EAF5', color: '#2E6494' },
    muted:   { bg: '#F5F2EC', color: '#4A5568' },
    default: { bg: '#F5F2EC', color: '#4A5568' },
  };

  const MAP = {
    lead: {
      NEW: 'info', CONTACTED: 'warn', QUALIFIED: 'success', CONVERTED: 'success', LOST: 'danger',
    },
    claim: {
      draft: 'muted', submitted: 'info', accepted: 'success', adjudicated: 'warn',
      paid: 'success', rejected: 'danger', partial: 'warn',
    },
    invoice: {
      draft: 'muted', issued: 'info', partial: 'warn', paid: 'success', void: 'danger', overdue: 'danger',
    },
    appointment: {
      SCHEDULED: 'info', CONFIRMED: 'success', COMPLETED: 'success', NO_SHOW: 'danger',
      PENDING: 'warn', PENDING_SYNC: 'warn', RESCHEDULED: 'warn', REMINDER_SENT: 'info', CANCELLED: 'danger',
    },
    lab_case: {
      draft: 'muted', sent: 'warn', in_progress: 'info', returned: 'success', remake: 'danger', cancelled: 'danger',
    },
    denture_case: {
      open: 'info', closed: 'muted',
    },
    treatment_plan: {
      draft: 'muted', presented: 'info', accepted: 'success', in_progress: 'warn', completed: 'success', declined: 'danger',
    },
    patient_lifecycle: {
      pending: 'warn', active: 'success', inactive: 'muted', deceased: 'danger', merged: 'muted',
    },
    recall: {
      pending: 'warn', sent: 'info', completed: 'success', cancelled: 'danger',
    },
  };

  const toneKey = (MAP[kind] && MAP[kind][value]) || 'default';
  const tone = TONES[toneKey];

  return (
    <span style={{
      display: 'inline-block',
      fontSize: '.66rem', fontWeight: 600, padding: '3px 10px', borderRadius: '999px',
      letterSpacing: '.06em', textTransform: 'uppercase',
      background: tone.bg, color: tone.color,
    }}>
      {value}
    </span>
  );
};

window.StatusPill = StatusPill;
