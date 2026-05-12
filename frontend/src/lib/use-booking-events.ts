'use client';
/**
 * useBookingEvents — subscribe to the backend's Server-Sent Events stream
 * and fire a toast for every "appointment.created" event.
 *
 * Why SSE: the new-booking popup needs to appear within ~1 second of the
 * write, including writes that originate outside the browser (the voice
 * AI booking through the dental-agent's calendar_client). Polling would
 * either burn requests or lag. SSE is one-direction, native to
 * EventSource, works through Cloud Run with no extra infra, and auto-
 * reconnects on transient drops.
 *
 * EventSource cannot send custom headers, so the clinic id rides as a
 * query param (matches the backend endpoint's contract).
 *
 * Mount once at AppShell level — duplicate mounts would open duplicate
 * connections and fire duplicate toasts.
 */

import { useEffect } from 'react';

import { API_BASE, getClinicId } from './api';
import { useToast } from '@/components/overlays/ToastContext';

interface AppointmentCreatedPayload {
  appointment_id: string;
  patient_name?: string;
  service_name?: string;
  provider_name?: string;
  start_time_local?: string; // e.g. "2026-05-12 09:00 AM"
}

/** One-line summary suitable for the toast detail. */
function formatBookingDetail(p: AppointmentCreatedPayload): string {
  const parts: string[] = [];
  if (p.service_name) parts.push(p.service_name);
  if (p.start_time_local) parts.push(p.start_time_local);
  if (p.provider_name) parts.push(`with ${p.provider_name}`);
  return parts.join(' · ');
}

export function useBookingEvents(): void {
  const { addToast } = useToast();

  useEffect(() => {
    // Skip on the server / during pre-render. EventSource only exists
    // in the browser; AppShell is a client component but a defensive
    // check protects against future SSR drift.
    if (typeof window === 'undefined' || typeof EventSource === 'undefined') {
      return;
    }

    const clinicId = getClinicId();
    const url = `${API_BASE}/api/v2/events/stream?clinic_id=${encodeURIComponent(clinicId)}`;
    const es = new EventSource(url);

    // The backend sends "appointment.created" as a named event.
    es.addEventListener('appointment.created', (ev: MessageEvent) => {
      try {
        const payload = JSON.parse(ev.data) as AppointmentCreatedPayload;
        const name = payload.patient_name || 'A new patient';
        addToast(`New booking — ${name}`, formatBookingDetail(payload));
      } catch (err) {
        // Malformed payload — log so we know the backend changed shape,
        // but don't surface to the user.
        console.warn('[useBookingEvents] bad appointment.created payload', err);
      }
    });

    // Generic onerror handles transient drops; EventSource auto-
    // reconnects with exponential backoff. We don't toast on errors
    // because reconnect storms during a deploy would spam the UI.
    es.onerror = () => {
      // Log only once per connection cycle.
      if (es.readyState === EventSource.CLOSED) {
        console.warn('[useBookingEvents] connection closed; browser will auto-retry');
      }
    };

    return () => {
      es.close();
    };
    // Re-subscribe only when the addToast identity changes (it's stable
    // per ToastProvider). Intentionally NOT re-running on clinic switch:
    // clinic id changes only on a hard navigation in this app's current
    // design — when that lands, add `clinicId` to the deps array.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [addToast]);
}
