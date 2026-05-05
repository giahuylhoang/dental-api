'use client';

import React from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import type { EventInput, EventDropArg, EventClickArg, DateSelectArg } from '@fullcalendar/core';
import type { EventResizeDoneArg } from '@fullcalendar/interaction';

export interface ScheduleEvent {
  id: string;
  title: string;
  start: string; // ISO
  end: string;   // ISO
  status?: string;
  providerId?: string;
  patient?: string;
  kind?: string;
}

export interface BusyBlockBg {
  id: string;
  daysOfWeek: number[];   // FullCalendar uses 0=Sun..6=Sat — caller converts
  startTime: string;      // HH:MM:SS
  endTime: string;        // HH:MM:SS
  label?: string;
}

interface Props {
  events: ScheduleEvent[];
  busy: BusyBlockBg[];
  initialDate?: string;
  onSelect: (start: Date, end: Date) => void;
  onEventClick: (id: string) => void;
  onEventDrop: (id: string, start: Date, end: Date) => void;
  onEventResize: (id: string, start: Date, end: Date) => void;
}

// Status-to-color mapping uses --primary, --steel, --success, --warning, --error tokens via inline color strings
// because FullCalendar expects literal hex/rgba on each event.
const STATUS_COLOR: Record<string, { bg: string; border: string; fg: string }> = {
  confirmed: { bg: '#3A7FBD', border: '#2E6494', fg: '#ffffff' },
  pending:   { bg: '#FDF3E5', border: '#B45309', fg: '#7A3A05' },
  no_show:   { bg: '#F8E5E8', border: '#9B2335', fg: '#5A1820' },
  completed: { bg: '#E8F5EE', border: '#2A7D4F', fg: '#1A5532' },
  cancelled: { bg: '#EDE9E0', border: '#8A9BB0', fg: '#4A5568' },
};

export default function ScheduleCalendar({ events, busy, initialDate, onSelect, onEventClick, onEventDrop, onEventResize }: Props) {
  const fcEvents: EventInput[] = [
    ...events.map(ev => {
      const palette = STATUS_COLOR[ev.status ?? 'confirmed'] ?? STATUS_COLOR.confirmed;
      return {
        id: ev.id,
        title: ev.title,
        start: ev.start,
        end: ev.end,
        backgroundColor: palette.bg,
        borderColor: palette.border,
        textColor: palette.fg,
        extendedProps: { status: ev.status, providerId: ev.providerId, patient: ev.patient, kind: ev.kind },
      } as EventInput;
    }),
    ...busy.map(b => ({
      id: b.id,
      groupId: 'busy',
      daysOfWeek: b.daysOfWeek,
      startTime: b.startTime,
      endTime: b.endTime,
      display: 'background' as const,
      backgroundColor: 'rgba(10,25,47,0.06)',
      title: b.label ?? '',
    })),
  ];

  const handleSelect = (arg: DateSelectArg) => {
    onSelect(arg.start, arg.end);
  };

  const handleEventClick = (arg: EventClickArg) => {
    onEventClick(arg.event.id);
  };

  const handleEventDrop = (arg: EventDropArg) => {
    if (!arg.event.start || !arg.event.end) { arg.revert(); return; }
    onEventDrop(arg.event.id, arg.event.start, arg.event.end);
  };

  const handleEventResize = (arg: EventResizeDoneArg) => {
    if (!arg.event.start || !arg.event.end) { arg.revert(); return; }
    onEventResize(arg.event.id, arg.event.start, arg.event.end);
  };

  return (
    <div className="rr-calendar">
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="timeGridWeek"
        initialDate={initialDate}
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay',
        }}
        buttonText={{ today: 'Today', month: 'Month', week: 'Week', day: 'Day' }}
        firstDay={1}
        selectable
        selectMirror
        editable
        eventResizableFromStart
        slotDuration="00:30:00"
        slotMinTime="07:00:00"
        slotMaxTime="20:00:00"
        nowIndicator
        weekNumbers={false}
        allDaySlot={false}
        height="calc(100vh - 220px)"
        events={fcEvents}
        select={handleSelect}
        eventClick={handleEventClick}
        eventDrop={handleEventDrop}
        eventResize={handleEventResize}
        slotLabelFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
        eventTimeFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
      />
    </div>
  );
}
