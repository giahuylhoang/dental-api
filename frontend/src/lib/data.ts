// Mock data — mirrors design_system/data/*.js shapes exactly

export interface Patient {
  id: string;
  first: string;
  last: string;
  dob: string;
  insurance: string;
  last_visit: string;
  status: 'active' | 'recall' | 'plan' | 'inactive';
}

export interface Appointment {
  id: string;
  time: string;
  duration: number;
  patient_id: string;
  patient: string;
  provider: string;
  chair: string;
  kind: string;
  status: 'confirmed' | 'pending' | 'no_show' | 'completed';
}

export interface Invoice {
  id: string;
  patient: string;
  total: number;
  balance: number;
  status: 'paid' | 'partial' | 'outstanding';
}

export interface LabCase {
  id: string;
  patient: string;
  vendor: string;
  item: string;
  eta: string;
  col: 'sent' | 'progress' | 'returned';
}

export const PATIENTS: Patient[] = [
  { id: 'P-018342', first: 'Alice', last: 'Stevens', dob: '1984-03-12', insurance: 'Alberta Blue Cross', last_visit: '2026-04-21', status: 'active' },
  { id: 'P-018298', first: 'Marcus', last: 'Doan', dob: '1971-09-04', insurance: 'Sun Life', last_visit: '2025-12-08', status: 'recall' },
  { id: 'P-018501', first: 'Priya', last: 'Khanna', dob: '1992-06-29', insurance: 'Manulife', last_visit: '2026-04-30', status: 'active' },
  { id: 'P-017901', first: 'Eli', last: 'Brouwer', dob: '2003-01-17', insurance: 'Canada Life', last_visit: '2026-02-12', status: 'plan' },
  { id: 'P-018611', first: 'Sofía', last: 'Castillo', dob: '1956-11-22', insurance: 'Alberta Health', last_visit: '2026-04-02', status: 'active' },
  { id: 'P-016102', first: 'Daniel', last: 'Okafor', dob: '1988-07-08', insurance: 'Pacific Blue Cross', last_visit: '2024-10-30', status: 'inactive' },
];

export const APPOINTMENTS: Appointment[] = [
  { id: 'A-1', time: '08:30', duration: 30, patient_id: 'P-018342', patient: 'Alice Stevens', provider: 'Dr Hau Le', chair: '1', kind: 'Recall · 6mo', status: 'confirmed' },
  { id: 'A-2', time: '09:00', duration: 60, patient_id: 'P-018501', patient: 'Priya Khanna', provider: 'Dr Hau Le', chair: '1', kind: 'Crown prep · #36', status: 'confirmed' },
  { id: 'A-3', time: '09:30', duration: 45, patient_id: 'P-018298', patient: 'Marcus Doan', provider: 'Dr Sara Lim', chair: '2', kind: 'Denture relines · upper', status: 'pending' },
  { id: 'A-4', time: '10:30', duration: 30, patient_id: 'P-017901', patient: 'Eli Brouwer', provider: 'Hyg. Renu', chair: '3', kind: 'Hygiene · scaling', status: 'confirmed' },
  { id: 'A-5', time: '11:00', duration: 90, patient_id: 'P-018611', patient: 'Sofía Castillo', provider: 'Dr Sara Lim', chair: '2', kind: 'Implant follow-up', status: 'confirmed' },
  { id: 'A-6', time: '13:00', duration: 60, patient_id: 'P-018342', patient: 'Alice Stevens', provider: 'Dr Hau Le', chair: '1', kind: 'Composite · MOD #14', status: 'no_show' },
  { id: 'A-7', time: '14:30', duration: 30, patient_id: 'P-016102', patient: 'Daniel Okafor', provider: 'Hyg. Renu', chair: '3', kind: 'New patient consult', status: 'pending' },
  { id: 'A-8', time: '15:30', duration: 45, patient_id: 'P-018501', patient: 'Priya Khanna', provider: 'Dr Hau Le', chair: '1', kind: 'Crown seat · #36', status: 'confirmed' },
];

export const INVOICES: Invoice[] = [
  { id: 'INV-2026-0872', patient: 'Alice Stevens', total: 420.00, balance: 0, status: 'paid' },
  { id: 'INV-2026-0870', patient: 'Priya Khanna', total: 1240.00, balance: 420.00, status: 'partial' },
  { id: 'INV-2026-0868', patient: 'Marcus Doan', total: 680.00, balance: 680.00, status: 'outstanding' },
  { id: 'INV-2026-0865', patient: 'Eli Brouwer', total: 195.00, balance: 0, status: 'paid' },
];

export const LAB_CASES: LabCase[] = [
  { id: 'LC-2026-0481', patient: 'Alice Stevens', vendor: 'Pinnacle Dental Lab', item: 'Crown · #36', eta: '2026-05-12', col: 'sent' },
  { id: 'LC-2026-0476', patient: 'Sofía Castillo', vendor: 'Crown City Lab', item: 'Implant · #11', eta: '2026-05-18', col: 'sent' },
  { id: 'LC-2026-0474', patient: 'Marcus Doan', vendor: 'Mountain Lab Services', item: 'Reline · upper denture', eta: '2026-05-08', col: 'progress' },
  { id: 'LC-2026-0469', patient: 'Priya Khanna', vendor: 'Pinnacle Dental Lab', item: 'Crown · #36', eta: '2026-05-04', col: 'returned' },
  { id: 'LC-2026-0467', patient: 'Eli Brouwer', vendor: 'Apex Ortho Lab', item: 'Retainer', eta: '2026-05-04', col: 'returned' },
];

export const LAB_COLUMNS = [
  { id: 'sent', label: 'Sent · waiting on lab', count: 3 },
  { id: 'progress', label: 'In progress', count: 2 },
  { id: 'returned', label: 'Returned · ready to seat', count: 4 },
];

export interface Provider {
  id: string;
  name: string;
  color: string;
  bg: string;
}

export interface ProviderWithOp {
  id: string;
  name: string;
  op: string;
}

export const PROVIDERS: Provider[] = [
  { id: '1', name: 'Dr Hau Le', color: '#3A7FBD', bg: '#D9EAF5' },
  { id: '2', name: 'Dr Sara Lim', color: '#2E6494', bg: '#A8CCE8' },
  { id: '3', name: 'Hyg. Renu', color: '#B45309', bg: '#FDF3E5' },
];

export const PROVIDER_OPTIONS: ProviderWithOp[] = [
  { id: 'hau', name: 'Dr Hau Le', op: 'Operatory 1' },
  { id: 'sara', name: 'Dr Sara Lim', op: 'Operatory 2' },
  { id: 'renu', name: 'Hyg. Renu', op: 'Operatory 3' },
];

// Mirrors database/models.py:120 ProviderBusyBlock — recurring weekly unavailable windows.
// weekday: 0=Mon ... 6=Sun (matches FullCalendar daysOfWeek when shifted: 1=Mon..0=Sun).
export interface BusyBlock {
  id: number;
  provider_id: number;
  weekday: number;
  start_hour: number;
  start_minute: number;
  end_hour: number;
  end_minute: number;
  label?: string;
}

export const BUSY_BLOCKS: BusyBlock[] = [
  // Lunch break for all providers, Mon-Fri
  { id: 1, provider_id: 1, weekday: 0, start_hour: 12, start_minute: 0, end_hour: 13, end_minute: 0, label: 'Lunch' },
  { id: 2, provider_id: 1, weekday: 1, start_hour: 12, start_minute: 0, end_hour: 13, end_minute: 0, label: 'Lunch' },
  { id: 3, provider_id: 1, weekday: 2, start_hour: 12, start_minute: 0, end_hour: 13, end_minute: 0, label: 'Lunch' },
  { id: 4, provider_id: 1, weekday: 3, start_hour: 12, start_minute: 0, end_hour: 13, end_minute: 0, label: 'Lunch' },
  { id: 5, provider_id: 1, weekday: 4, start_hour: 12, start_minute: 0, end_hour: 13, end_minute: 0, label: 'Lunch' },
  // Dr Sara only available Tue/Thu mornings, blocked rest of week mornings
  { id: 6, provider_id: 2, weekday: 0, start_hour: 7, start_minute: 0, end_hour: 9, end_minute: 0, label: 'Hospital rounds' },
  { id: 7, provider_id: 2, weekday: 2, start_hour: 7, start_minute: 0, end_hour: 9, end_minute: 0, label: 'Hospital rounds' },
  // Hyg. Renu admin block Wed afternoon
  { id: 8, provider_id: 3, weekday: 2, start_hour: 14, start_minute: 0, end_hour: 17, end_minute: 0, label: 'Admin / education' },
];

export interface Notification {
  id: number;
  text: string;
  time: string;
  read: boolean;
}

export const NOTIFICATIONS: Notification[] = [
  { id: 1, text: 'Alice Stevens confirmed her 08:30 appointment.', time: '2 min ago', read: false },
  { id: 2, text: 'Lab case LC-2026-0469 returned from Pinnacle Dental Lab.', time: '18 min ago', read: false },
  { id: 3, text: 'Recall reminder sent to Marcus Doan.', time: '1 hr ago', read: true },
  { id: 4, text: 'Invoice INV-2026-0870 partial payment received.', time: '3 hr ago', read: true },
];

// Tooth chart data
export const TOOTH_STATUS: Record<string, { fill: string; stroke: string }> = {
  sound: { fill: '#fff', stroke: '#C8CCCC' },
  caries: { fill: '#FDF3E5', stroke: '#B45309' },
  resto: { fill: '#D9EAF5', stroke: '#3A7FBD' },
  crown: { fill: '#A8CCE8', stroke: '#2E6494' },
  miss: { fill: '#EDE9E0', stroke: '#8A9BB0' },
  endo: { fill: '#F8E5E8', stroke: '#9B2335' },
};

export const MARKINGS: Record<number, string> = {
  16: 'resto', 17: 'caries', 26: 'crown', 27: 'resto',
  36: 'crown', 37: 'caries', 46: 'resto', 47: 'sound',
  31: 'sound', 41: 'sound', 11: 'sound', 21: 'sound',
  18: 'miss', 28: 'miss', 38: 'miss', 48: 'miss',
};

export const UPPER = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
export const LOWER = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

// CRM Leads
export interface Lead {
  id: string;
  name: string;
  phone: string;
  email: string;
  source: string;
  status: 'new' | 'contacted' | 'qualified' | 'converted' | 'lost';
  notes: string;
  created: string;
}

export const LEADS: Lead[] = [
  { id: 'L-101', name: 'Robert Chen', phone: '403-555-0101', email: 'rc@email.com', source: 'Website', status: 'new', notes: 'Looking for full denture replacement', created: '2026-05-01' },
  { id: 'L-102', name: 'Maria Santos', phone: '403-555-0102', email: 'ms@email.com', source: 'Referral', status: 'contacted', notes: 'Interested in implant consult', created: '2026-04-28' },
  { id: 'L-103', name: 'James Wright', phone: '403-555-0103', email: 'jw@email.com', source: 'Google', status: 'qualified', notes: 'Has insurance, wants crown work', created: '2026-04-25' },
  { id: 'L-104', name: 'Linda Park', phone: '403-555-0104', email: 'lp@email.com', source: 'Yelp', status: 'converted', notes: 'Booked recall appointment', created: '2026-04-20' },
];

export interface Recall {
  id: string;
  patient: string;
  due_date: string;
  type: string;
  status: 'pending' | 'sent' | 'confirmed';
}

export const RECALLS: Recall[] = [
  { id: 'R-1', patient: 'Marcus Doan', due_date: '2026-05-15', type: '6-month recall', status: 'pending' },
  { id: 'R-2', patient: 'Eli Brouwer', due_date: '2026-05-20', type: '12-month recall', status: 'sent' },
  { id: 'R-3', patient: 'Daniel Okafor', due_date: '2026-06-01', type: '6-month recall', status: 'pending' },
];

export interface Thread {
  id: string;
  patient: string;
  subject: string;
  last_message: string;
  time: string;
  unread: boolean;
  channel: 'sms' | 'email' | 'voice';
}

export const THREADS: Thread[] = [
  { id: 'T-1', patient: 'Alice Stevens', subject: 'Appointment reminder', last_message: 'Yes, I confirm my 08:30 slot.', time: '10 min ago', unread: true, channel: 'sms' },
  { id: 'T-2', patient: 'Priya Khanna', subject: 'Insurance pre-auth', last_message: 'Pre-authorization approved for crown #36.', time: '2 hr ago', unread: false, channel: 'email' },
  { id: 'T-3', patient: 'Marcus Doan', subject: 'Recall reminder', last_message: 'Patient requested to reschedule.', time: '1 day ago', unread: true, channel: 'sms' },
];

// Sidebar nav config (matches Sidebar.jsx exactly)
export interface NavItem {
  key: string;
  label: string;
  href: string;
  group: string;
  icon: string;
  isNew?: boolean;
}

export const NAV: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', href: '/dashboard', group: 'Care', icon: 'LayoutDashboard' },
  { key: 'patients', label: 'Patients', href: '/patients', group: 'Care', icon: 'Users' },
  { key: 'schedule', label: 'Schedule', href: '/schedule', group: 'Care', icon: 'Calendar' },
  { key: 'plans', label: 'Treatment', href: '/treatment', group: 'Care', icon: 'ClipboardList' },
  { key: 'lab', label: 'Lab', href: '/lab', group: 'Care', icon: 'FlaskConical' },
  { key: 'billing', label: 'Billing', href: '/billing', group: 'Operations', icon: 'DollarSign' },
  { key: 'comms', label: 'Communications', href: '/communications', group: 'Operations', icon: 'MessageCircle' },
  { key: 'crm', label: 'CRM', href: '/crm', group: 'Operations', icon: 'UserRoundPlus' },
  { key: 'reports', label: 'Reports', href: '/reports', group: 'Insights', icon: 'ChartLine' },
  { key: 'ai-receptionist', label: 'AI Receptionist', href: '/login?next=_prototype/admin-dashboard', group: 'Operations', isNew: true, icon: 'Mic' },
  { key: 'settings', label: 'Settings', href: '/settings', group: 'System', icon: 'Settings' },
];

export const GROUP_ORDER = ['Care', 'Operations', 'Insights', 'System'];
