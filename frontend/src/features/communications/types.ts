export type Channel = 'sms' | 'email' | 'whatsapp';

export interface Message {
  id: string;
  patient_id: string;
  channel: Channel;
  direction: 'inbound' | 'outbound';
  body: string;
  status: string;
  created_at: string;
  read_at?: string | null;
  patient_name?: string;
  from?: string;
  thread_key?: string;
}

export interface Thread {
  thread_key: string;
  patient_id: string;
  patient_name: string;
  channel: Channel;
  messages: Message[];
  last_at: string;
}
