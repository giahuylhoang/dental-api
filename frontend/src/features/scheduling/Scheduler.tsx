import { useRef, useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import type { DateSelectArg, EventDropArg } from '@fullcalendar/core';
import type { EventClickArg, EventInput } from '@fullcalendar/core';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetcher } from '../../api/client';
import { useAuthStore } from '../auth/store';
import AppointmentDrawer from './AppointmentDrawer';
import NewAppointmentDialog from './NewAppointmentDialog';

interface CalEvent {
  id: string;
  title: string;
  start: string;
  end: string;
}

export default function Scheduler() {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const calRef = useRef<FullCalendar>(null);

  const [drawerApptId, setDrawerApptId] = useState<string | null>(null);
  const [newApptRange, setNewApptRange] = useState<{ start: string; end: string } | null>(null);

  // Fetch events for the visible range — FullCalendar calls this via `events` function
  const { data: events = [] } = useQuery<CalEvent[]>({
    queryKey: ['calendar-events', clinicId],
    queryFn: () => {
      const now = new Date();
      const start = new Date(now);
      start.setDate(now.getDate() - 7);
      const end = new Date(now);
      end.setDate(now.getDate() + 30);
      return fetcher<CalEvent[]>(
        `/api/calendar/events?start=${start.toISOString()}&end=${end.toISOString()}`,
      );
    },
  });

  const reschedule = useMutation({
    mutationFn: ({ id, start, end }: { id: string; start: string; end: string }) =>
      fetcher(`/api/appointments/${id}/reschedule`, {
        method: 'PUT',
        body: JSON.stringify({ start_time: start, end_time: end }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['calendar-events', clinicId] }),
  });

  function handleSelect(arg: DateSelectArg) {
    setNewApptRange({
      start: arg.startStr,
      end: arg.endStr,
    });
  }

  function handleEventClick(arg: EventClickArg) {
    setDrawerApptId(arg.event.id);
  }

  function handleEventDrop(arg: EventDropArg) {
    const { event } = arg;
    reschedule.mutate({
      id: event.id,
      start: event.startStr,
      end: event.endStr ?? event.startStr,
    });
  }

  const fcEvents: EventInput[] = events.map((e) => ({
    id: e.id,
    title: e.title,
    start: e.start,
    end: e.end,
  }));

  // Expose calendar API for e2e tests via effect
  useEffect(() => {
    if (typeof window !== 'undefined' && calRef.current) {
      (window as unknown as Record<string, unknown>)['__fc'] = calRef.current.getApi();
    }
  });

  return (
    <>
      <FullCalendar
        ref={calRef}
        plugins={[timeGridPlugin, dayGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay',
        }}
        slotDuration="00:15:00"
        selectable
        editable
        events={fcEvents}
        select={handleSelect}
        eventClick={handleEventClick}
        eventDrop={handleEventDrop}
      />

      <AppointmentDrawer
        appointmentId={drawerApptId}
        open={!!drawerApptId}
        onClose={() => setDrawerApptId(null)}
        onChanged={() => qc.invalidateQueries({ queryKey: ['calendar-events', clinicId] })}
      />

      <NewAppointmentDialog
        key={newApptRange ? `${newApptRange.start}-${newApptRange.end}` : 'closed'}
        open={!!newApptRange}
        start={newApptRange?.start ?? ''}
        end={newApptRange?.end ?? ''}
        onClose={() => setNewApptRange(null)}
        onCreated={() => {
          setNewApptRange(null);
          qc.invalidateQueries({ queryKey: ['calendar-events', clinicId] });
        }}
      />
    </>
  );
}
