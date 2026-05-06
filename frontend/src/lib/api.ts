/**
 * Typed HTTP client for the dental-api backend.
 *
 * Notes
 * - Base URL: NEXT_PUBLIC_API_BASE (defaults to http://localhost:8001).
 * - Multi-tenancy: every request injects the X-Clinic-Id header. The clinic id
 *   resolves from localStorage("clinicId") at runtime, falling back to "default".
 *   Server-side renders (no localStorage) always use "default".
 * - Error policy: non-2xx responses throw `ApiError` with `.status`, `.body`
 *   (parsed JSON if available), and the original `Response`.
 * - Mock fallback: callers can opt into mocks by checking
 *   `process.env.NEXT_PUBLIC_USE_MOCKS === '1'` and using lib/data.ts instead.
 *   The client itself never silently falls back; it always hits the network.
 *
 * The grouping under `api.*` mirrors the backend router shape so a feature can
 * be moved from mocks to live data with one import swap.
 */

export const API_BASE: string =
  (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_BASE) ||
  'http://localhost:8001';

const DEFAULT_CLINIC_ID = 'default';

export function getClinicId(): string {
  if (typeof window === 'undefined') return DEFAULT_CLINIC_ID;
  try {
    return window.localStorage.getItem('clinicId') || DEFAULT_CLINIC_ID;
  } catch {
    return DEFAULT_CLINIC_ID;
  }
}

export function setClinicId(id: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem('clinicId', id);
  } catch {
    /* swallow — non-essential */
  }
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number;
  body: unknown;
  response: Response;
  requestId?: string;
  constructor(message: string, response: Response, body: unknown, requestId?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = response.status;
    this.body = body;
    this.response = response;
    this.requestId = requestId;
  }
}

// ---------------------------------------------------------------------------
// Dev-only trace buffer
// ---------------------------------------------------------------------------

interface TraceEntry {
  ts: string;
  method: string;
  path: string;
  status: number;
  requestId: string;
  durationMs: number;
}

declare global {
  // eslint-disable-next-line no-var
  var __dental: { lastTrace: TraceEntry[] } | undefined;
}

function recordTrace(entry: TraceEntry): void {
  if (process.env.NODE_ENV === 'production') return;
  if (typeof globalThis === 'undefined') return;
  globalThis.__dental ||= { lastTrace: [] };
  globalThis.__dental.lastTrace.push(entry);
  // Keep only last 50 entries
  if (globalThis.__dental.lastTrace.length > 50) {
    globalThis.__dental.lastTrace.shift();
  }
}

// ---------------------------------------------------------------------------
// Core fetch
// ---------------------------------------------------------------------------

interface FetchInit extends Omit<RequestInit, 'body'> {
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
}

function buildUrl(path: string, query?: FetchInit['query']): string {
  const url = new URL(path.startsWith('http') ? path : API_BASE + path);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

export async function apiFetch<T = unknown>(path: string, init: FetchInit = {}): Promise<T> {
  const { body, query, headers, ...rest } = init;
  const url = buildUrl(path, query);

  // Generate request ID for tracing
  const requestId = typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  const finalHeaders: Record<string, string> = {
    'X-Clinic-Id': getClinicId(),
    'X-Request-Id': requestId,
    Accept: 'application/json',
    ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
    ...((headers as Record<string, string>) || {}),
  };

  const startTime = performance.now();
  const res = await fetch(url, {
    ...rest,
    headers: finalHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const durationMs = performance.now() - startTime;

  // Get echoed request ID from server (may differ if server generated one)
  const echoedRequestId = res.headers.get('X-Request-Id') || requestId;

  // Record trace in dev mode
  recordTrace({
    ts: new Date().toISOString(),
    method: (rest.method || 'GET').toUpperCase(),
    path: new URL(url).pathname,
    status: res.status,
    requestId: echoedRequestId,
    durationMs: Math.round(durationMs),
  });

  if (res.status === 204) {
    return undefined as T;
  }

  // Try to parse JSON; tolerate empty bodies.
  let parsed: unknown = undefined;
  const text = await res.text();
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!res.ok) {
    const detail = (parsed && typeof parsed === 'object' && 'detail' in parsed
      ? String((parsed as { detail: unknown }).detail)
      : res.statusText) || `HTTP ${res.status}`;
    throw new ApiError(`${res.status} ${detail}`, res, parsed, echoedRequestId);
  }

  return parsed as T;
}

// ---------------------------------------------------------------------------
// Shared types — kept loose where the backend response is large; tighten as
// pages adopt them.
// ---------------------------------------------------------------------------

export interface PatientDTO {
  id: string;
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  email?: string | null;
}

export interface AppointmentDTO {
  id: string;
  start_time: string;
  end_time: string;
  patient_id: string;
  provider_id: number;
  service_id?: number | null;
  status: string;
  patient_name?: string | null;
  service_name?: string | null;
  reason_note?: string | null;
}

export interface ProviderDTO {
  id: number;
  name: string;
  title?: string | null;
  specialty?: string | null;
  is_active?: boolean;
}

export interface ServiceDTO {
  id: number;
  name: string;
  duration_min?: number | null;
  base_price?: number | null;
}

export interface LeadDTO {
  id: string;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  source?: string | null;
  status: string;
  notes?: string | null;
}

export interface ClinicConfigDTO {
  display_name?: string | null;
  timezone?: string | null;
  working_hour_start?: number | null;
  working_hour_end?: number | null;
  address?: string | null;
  contact_phone?: string | null;
  booking_notification_email?: string | null;
}

export interface AiVoiceDTO {
  assistant_name: string;
  provider_title: string;
  reason_question: string;
  language: string;
}

export interface AiDisclosureDTO {
  required: boolean;
  phrase: string;
  last_reviewed_at: string | null;
}

export interface ServiceBookableDTO {
  service_id: number;
  name: string;
  duration_min: number | null;
  base_price: number | null;
  bookable: boolean;
}

export interface KnowledgeListItemDTO {
  filename: string;
  title: string;
  word_count: number;
  updated_at: string | null;
}

export interface KnowledgeDocDTO extends KnowledgeListItemDTO {
  body: string;
}

export interface BusyBlockDTO {
  id: number;
  provider_id: number;
  weekday: number;       // 0=Mon..6=Sun (matches backend)
  start_hour: number;
  start_minute: number;
  end_hour: number;
  end_minute: number;
  label: string | null;
}

// ---------------------------------------------------------------------------
// API surface
// ---------------------------------------------------------------------------

export const api = {
  // ── v1 (locked — calendar_client.py contract) ─────────────────────────
  patients: {
    list: (params?: { phone?: string; email?: string }) =>
      apiFetch<PatientDTO[]>('/api/patients', { query: params }),
    get: (id: string) => apiFetch<PatientDTO>(`/api/patients/${id}`),
    create: (data: Partial<PatientDTO>) =>
      apiFetch<PatientDTO>('/api/patients', { method: 'POST', body: data }),
    update: (id: string, data: Partial<PatientDTO>) =>
      apiFetch<PatientDTO>(`/api/patients/${id}`, { method: 'PUT', body: data }),
    verify: (phone: string, dob: string) =>
      apiFetch<{ patient_id: string; verified: boolean }>('/api/patients/verify', {
        method: 'POST',
        body: { phone, dob },
      }),
  },

  appointments: {
    list: (params?: Record<string, string | number | undefined>) =>
      apiFetch<AppointmentDTO[]>('/api/appointments', { query: params }),
    get: (id: string) => apiFetch<AppointmentDTO>(`/api/appointments/${id}`),
    create: (data: Omit<AppointmentDTO, 'id' | 'status'> & { reason: string; patient_name: string; service_name: string }) =>
      apiFetch<{ appointment_id: string; calendar_event_id?: string; status: string }>(
        '/api/calendar/events',
        { method: 'POST', body: data },
      ),
    update: (id: string, updates: Partial<AppointmentDTO>) =>
      apiFetch<AppointmentDTO>(`/api/appointments/${id}`, { method: 'PUT', body: updates }),
    cancel: (id: string) =>
      apiFetch<{ status: string }>(`/api/appointments/${id}/cancel`, { method: 'PUT' }),
    reschedule: (id: string, data: Omit<AppointmentDTO, 'id' | 'status'> & { reason: string; patient_name: string; service_name: string }) =>
      apiFetch<{ old_appointment_id: string; new_appointment_id: string; status: string }>(
        `/api/appointments/${id}/reschedule`,
        { method: 'PUT', body: data },
      ),
    setStatus: (id: string, status: string) =>
      apiFetch<AppointmentDTO>(`/api/appointments/${id}/status`, {
        method: 'PUT',
        body: { status },
      }),
  },

  providers: {
    list: () => apiFetch<ProviderDTO[]>('/api/providers'),
    get: (id: number) => apiFetch<ProviderDTO>(`/api/providers/${id}`),
  },

  services: {
    list: (name?: string) => apiFetch<ServiceDTO[]>('/api/services', { query: { name } }),
    get: (id: number) => apiFetch<ServiceDTO>(`/api/services/${id}`),
  },

  slots: {
    available: (params: {
      start_datetime: string;
      end_datetime: string;
      provider_id?: number;
      provider_name?: string;
      slot_minutes?: number;
    }) => apiFetch<unknown>('/api/calendar/slots', { query: params }),
  },

  leads: {
    list: (params?: { status?: string; source?: string }) =>
      apiFetch<LeadDTO[]>('/api/leads', { query: params }),
    get: (id: string) => apiFetch<LeadDTO>(`/api/leads/${id}`),
    create: (data: Partial<LeadDTO>) =>
      apiFetch<LeadDTO>('/api/leads', { method: 'POST', body: data }),
    update: (id: string, data: Partial<LeadDTO>) =>
      apiFetch<LeadDTO>(`/api/leads/${id}`, { method: 'PUT', body: data }),
    setStatus: (id: string, status: string) =>
      apiFetch<LeadDTO>(`/api/leads/${id}/status`, { method: 'PUT', body: { status } }),
  },

  // ── v2 ────────────────────────────────────────────────────────────────
  v2: {
    settings: {
      clinic: {
        get: () => apiFetch<ClinicConfigDTO>('/api/v2/settings/clinic'),
        update: (patch: Partial<ClinicConfigDTO>) =>
          apiFetch<ClinicConfigDTO>('/api/v2/settings/clinic', { method: 'PUT', body: patch }),
      },
      integrations: () =>
        apiFetch<{ sms: { enabled: boolean }; email: { enabled: boolean }; whatsapp: { enabled: boolean } }>(
          '/api/v2/settings/integrations',
        ),
      ai: {
        voice: {
          get: () => apiFetch<AiVoiceDTO>('/api/v2/settings/ai/voice'),
          update: (patch: Partial<AiVoiceDTO>) =>
            apiFetch<AiVoiceDTO>('/api/v2/settings/ai/voice', { method: 'PUT', body: patch }),
        },
        disclosure: {
          get: () => apiFetch<AiDisclosureDTO>('/api/v2/settings/ai/disclosure'),
          update: (patch: Partial<Pick<AiDisclosureDTO, 'required' | 'phrase'>>) =>
            apiFetch<AiDisclosureDTO>('/api/v2/settings/ai/disclosure', { method: 'PUT', body: patch }),
        },
        servicesBookable: {
          list: () => apiFetch<ServiceBookableDTO[]>('/api/v2/settings/ai/services-bookable'),
          set: (serviceId: number, bookable: boolean) =>
            apiFetch<ServiceBookableDTO>(`/api/v2/settings/ai/services-bookable/${serviceId}`, {
              method: 'PUT',
              body: { bookable },
            }),
        },
        knowledge: {
          list: () => apiFetch<KnowledgeListItemDTO[]>('/api/v2/settings/ai/knowledge'),
          get: (filename: string) =>
            apiFetch<KnowledgeDocDTO>(`/api/v2/settings/ai/knowledge/${encodeURIComponent(filename)}`),
          create: (data: { filename: string; title: string; body: string }) =>
            apiFetch<KnowledgeDocDTO>('/api/v2/settings/ai/knowledge', { method: 'POST', body: data }),
          update: (filename: string, data: Partial<{ title: string; body: string }>) =>
            apiFetch<KnowledgeDocDTO>(
              `/api/v2/settings/ai/knowledge/${encodeURIComponent(filename)}`,
              { method: 'PUT', body: data },
            ),
          delete: (filename: string) =>
            apiFetch<void>(`/api/v2/settings/ai/knowledge/${encodeURIComponent(filename)}`, {
              method: 'DELETE',
            }),
        },
      },
    },

    // Coarse-grained passthroughs for the larger surfaces — pages can refine
    // their own typed wrappers as they adopt these endpoints.
    scheduling: {
      operatories: {
        list: () => apiFetch<unknown[]>('/api/v2/scheduling/operatories'),
        create: (data: unknown) =>
          apiFetch<unknown>('/api/v2/scheduling/operatories', { method: 'POST', body: data }),
        update: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/scheduling/operatories/${id}`, { method: 'PUT', body: data }),
        delete: (id: string) =>
          apiFetch<void>(`/api/v2/scheduling/operatories/${id}`, { method: 'DELETE' }),
      },
      calendar: (params: { from?: string; to?: string }) =>
        apiFetch<unknown>('/api/v2/scheduling/calendar', { query: params }),
      waitlist: {
        list: () => apiFetch<unknown[]>('/api/v2/scheduling/waitlist'),
        add: (data: unknown) =>
          apiFetch<unknown>('/api/v2/scheduling/waitlist', { method: 'POST', body: data }),
        remove: (id: string) =>
          apiFetch<void>(`/api/v2/scheduling/waitlist/${id}`, { method: 'DELETE' }),
      },
      recallRules: {
        list: () => apiFetch<unknown[]>('/api/v2/scheduling/recall-rules'),
        create: (data: unknown) =>
          apiFetch<unknown>('/api/v2/scheduling/recall-rules', { method: 'POST', body: data }),
        update: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/scheduling/recall-rules/${id}`, { method: 'PUT', body: data }),
        delete: (id: string) =>
          apiFetch<void>(`/api/v2/scheduling/recall-rules/${id}`, { method: 'DELETE' }),
      },
      recalls: () => apiFetch<unknown[]>('/api/v2/scheduling/recalls'),
      busyBlocks: {
        list: (params?: { provider_id?: number }) =>
          apiFetch<BusyBlockDTO[]>('/api/v2/scheduling/busy-blocks', { query: params }),
        create: (data: Omit<BusyBlockDTO, 'id'>) =>
          apiFetch<BusyBlockDTO>('/api/v2/scheduling/busy-blocks', { method: 'POST', body: data }),
        update: (id: number, data: Partial<Omit<BusyBlockDTO, 'id'>>) =>
          apiFetch<BusyBlockDTO>(`/api/v2/scheduling/busy-blocks/${id}`, { method: 'PUT', body: data }),
        delete: (id: number) =>
          apiFetch<void>(`/api/v2/scheduling/busy-blocks/${id}`, { method: 'DELETE' }),
      },
    },

    treatmentPlans: {
      list: () => apiFetch<unknown[]>('/api/v2/treatment_plans'),
      get: (id: string) => apiFetch<unknown>(`/api/v2/treatment_plans/${id}`),
      create: (data: unknown) =>
        apiFetch<unknown>('/api/v2/treatment_plans', { method: 'POST', body: data }),
      patchItems: (id: string, data: unknown) =>
        apiFetch<unknown>(`/api/v2/treatment_plans/${id}/items`, { method: 'PATCH', body: data }),
      present: (id: string) =>
        apiFetch<unknown>(`/api/v2/treatment_plans/${id}/present`, { method: 'POST' }),
      accept: (id: string) =>
        apiFetch<unknown>(`/api/v2/treatment_plans/${id}/accept`, { method: 'POST' }),
      decline: (id: string) =>
        apiFetch<unknown>(`/api/v2/treatment_plans/${id}/decline`, { method: 'POST' }),
      complete: (id: string) =>
        apiFetch<unknown>(`/api/v2/treatment_plans/${id}/complete`, { method: 'POST' }),
    },

    lab: {
      vendors: {
        list: () => apiFetch<unknown[]>('/api/v2/lab/vendors'),
        create: (data: unknown) =>
          apiFetch<unknown>('/api/v2/lab/vendors', { method: 'POST', body: data }),
        update: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/lab/vendors/${id}`, { method: 'PUT', body: data }),
        delete: (id: string) =>
          apiFetch<void>(`/api/v2/lab/vendors/${id}`, { method: 'DELETE' }),
      },
      cases: {
        list: () => apiFetch<unknown[]>('/api/v2/lab/cases'),
        create: (data: unknown) =>
          apiFetch<unknown>('/api/v2/lab/cases', { method: 'POST', body: data }),
        setStatus: (id: string, status: string) =>
          apiFetch<unknown>(`/api/v2/lab/cases/${id}/status`, {
            method: 'PATCH',
            body: { status },
          }),
        send: (id: string) =>
          apiFetch<unknown>(`/api/v2/lab/cases/${id}/send`, { method: 'POST' }),
        return: (id: string) =>
          apiFetch<unknown>(`/api/v2/lab/cases/${id}/return`, { method: 'POST' }),
        remake: (id: string) =>
          apiFetch<unknown>(`/api/v2/lab/cases/${id}/remake`, { method: 'POST' }),
      },
    },

    billing: {
      invoices: {
        list: () => apiFetch<unknown[]>('/api/v2/billing/invoices'),
        get: (id: string) => apiFetch<unknown>(`/api/v2/billing/invoices/${id}`),
        create: (data: unknown) =>
          apiFetch<unknown>('/api/v2/billing/invoices', { method: 'POST', body: data }),
        issue: (id: string) =>
          apiFetch<unknown>(`/api/v2/billing/invoices/${id}/issue`, { method: 'POST' }),
        pay: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/billing/invoices/${id}/payments`, { method: 'POST', body: data }),
        void: (id: string) =>
          apiFetch<unknown>(`/api/v2/billing/invoices/${id}/void`, { method: 'POST' }),
        fromPlan: (data: unknown) =>
          apiFetch<unknown>('/api/v2/billing/invoices/from-plan', { method: 'POST', body: data }),
      },
    },

    insurance: {
      claims: {
        list: () => apiFetch<unknown[]>('/api/v2/insurance/claims'),
        create: (data: unknown) =>
          apiFetch<unknown>('/api/v2/insurance/claims', { method: 'POST', body: data }),
        submit: (id: string) =>
          apiFetch<unknown>(`/api/v2/insurance/claims/${id}/submit`, { method: 'POST' }),
        adjudicate: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/insurance/claims/${id}/adjudicate`, { method: 'POST', body: data }),
        markPaid: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/insurance/claims/${id}/mark-paid`, { method: 'POST', body: data }),
      },
    },

    communications: {
      list: () => apiFetch<unknown[]>('/api/v2/communications'),
      send: (data: unknown) =>
        apiFetch<unknown>('/api/v2/communications/send', { method: 'POST', body: data }),
      threadRead: (key: string) =>
        apiFetch<unknown>(`/api/v2/communications/threads/${encodeURIComponent(key)}/read`, {
          method: 'PATCH',
        }),
    },

    crm: {
      leads: {
        list: () => apiFetch<unknown[]>('/api/v2/crm/leads'),
        get: (id: string) => apiFetch<unknown>(`/api/v2/crm/leads/${id}`),
        create: (data: unknown) =>
          apiFetch<unknown>('/api/v2/crm/leads', { method: 'POST', body: data }),
        update: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/crm/leads/${id}`, { method: 'PUT', body: data }),
        addActivity: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/crm/leads/${id}/activities`, { method: 'POST', body: data }),
        listActivities: (id: string) =>
          apiFetch<unknown[]>(`/api/v2/crm/leads/${id}/activities`),
        convert: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/crm/leads/${id}/convert`, { method: 'POST', body: data }),
      },
    },

    clinical: {
      toothChart: {
        get: (patientId: string) =>
          apiFetch<unknown[]>(`/api/v2/clinical/patients/${patientId}/tooth-chart`),
        set: (patientId: string, data: unknown) =>
          apiFetch<unknown[]>(`/api/v2/clinical/patients/${patientId}/tooth-chart`, {
            method: 'POST',
            body: data,
          }),
      },
      notes: {
        list: () => apiFetch<unknown[]>('/api/v2/clinical/notes'),
        create: (data: unknown) =>
          apiFetch<unknown>('/api/v2/clinical/notes', { method: 'POST', body: data }),
        amend: (id: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/clinical/notes/${id}/amend`, { method: 'POST', body: data }),
        lock: (id: string) =>
          apiFetch<unknown>(`/api/v2/clinical/notes/${id}/lock`, { method: 'POST' }),
      },
      insurance: {
        list: (patientId: string) =>
          apiFetch<unknown[]>(`/api/v2/clinical/patients/${patientId}/insurance`),
        create: (patientId: string, data: unknown) =>
          apiFetch<unknown>(`/api/v2/clinical/patients/${patientId}/insurance`, {
            method: 'POST',
            body: data,
          }),
      },
      documents: {
        list: (patientId: string) =>
          apiFetch<unknown[]>(`/api/v2/clinical/patients/${patientId}/documents`),
      },
    },

    reporting: {
      kpi: () => apiFetch<unknown>('/api/v2/reporting/kpi'),
      productionByProvider: () => apiFetch<unknown>('/api/v2/reporting/production-by-provider'),
      remakeRateByLab: () => apiFetch<unknown>('/api/v2/reporting/remake-rate-by-lab'),
    },
  },
};
