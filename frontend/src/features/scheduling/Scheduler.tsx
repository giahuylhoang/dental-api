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
import { PageHeader } from '@/components/ui/page-header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import './scheduler.css';

interface CalEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  patient_id?: string;
  status?: string;
}

interface Doctor {
  id: number;
  name: string;
}

interface Service {
  id: number;
  name: string;
}

interface Patient {
  id: string;
  first_name: string;
  last_name: string;
}

const STATUS_COLORS: Record<string, string> = {
  scheduled: 'bg-blue-100 text-blue-800',
  confirmed: 'bg-green-100 text-green-800',
  completed: 'bg-zinc-100 text-zinc-800',
  cancelled: 'bg-red-100 text-red-800',
  'no-show': 'bg-amber-100 text-amber-800',
};

function getWeekRange(): string {
  const now = new Date();
  const start = new Date(now);
  start.setDate(now.getDate() - now.getDay());
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
}

export default function Scheduler() {
  const clinicId = useAuthStore((s) => s.clinicId);
  const qc = useQueryClient();
  const calRef = useRef<FullCalendar>(null);

  const [drawerApptId, setDrawerApptId] = useState<string | null>(null);
  const [newApptRange, setNewApptRange] = useState<{ start: string; end: string } | null>(null);
  const [providerFilter, setProviderFilter] = useState('all');
  const [serviceFilter, setServiceFilter] = useState('all');
  const [activeView, setActiveView] = useState<'Day' | 'Week' | 'Month'>('Week');

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

  const { data: doctors = [] } = useQuery<Doctor[]>({
    queryKey: ['doctors', clinicId],
    queryFn: () => fetcher<Doctor[]>('/api/doctors'),
  });

  const { data: services = [] } = useQuery<Service[]>({
    queryKey: ['services', clinicId],
    queryFn: () => fetcher<Service[]>('/api/services'),
  });

  // Bulk-resolve patient names to avoid N+1
  const patientIds = [...new Set(events.map((e) => e.patient_id).filter(Boolean))] as string[];
  const { data: patientsData } = useQuery<{ items: Patient[] }>({
    queryKey: ['patients-by-ids', patientIds],
    queryFn: () =>
      patientIds.length > 0
        ? fetcher<{ items: Patient[] }>(`/api/patients?ids=${patientIds.join(',')}`)
        : Promise.resolve({ items: [] }),
    enabled: patientIds.length > 0,
  });

  const patientMap = new Map<string, Patient>(
    (patientsData?.items ?? []).map((p) => [p.id, p]),
  );

  const reschedule = useMutation({
    mutationFn: ({ id, start, end }: { id: string; start: string; end: string }) =>
      fetcher(`/api/appointments/${id}/reschedule`, {
        method: 'PUT',
        body: JSON.stringify({ start_time: start, end_time: end }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['calendar-events', clinicId] }),
  });

  function handleSelect(arg: DateSelectArg) {
    setNewApptRange({ start: arg.startStr, end: arg.endStr });
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

  function handleViewChange(view: 'Day' | 'Week' | 'Month') {
    setActiveView(view);
    const viewMap = { Day: 'timeGridDay', Week: 'timeGridWeek', Month: 'dayGridMonth' } as const;
    const targetView = viewMap[view];
    // Notify test hooks
    const win = window as unknown as Record<string, ((v: string) => void) | undefined>;
    win['__onViewChange']?.(targetView);
    // Call FullCalendar API
    const calApi = calRef.current?.getApi();
    if (calApi) {
      calApi.changeView(targetView);
    } else {
      const fc = (window as unknown as Record<string, { changeView: (v: string) => void } | undefined>)['__fc'];
      fc?.changeView(targetView);
    }
  }

  const fcEvents: EventInput[] = events.map((e) => {
    const patient = e.patient_id ? patientMap.get(e.patient_id) : undefined;
    const patientName = patient ? `${patient.first_name} ${patient.last_name}` : '';
    const title = patientName ? `${patientName} — ${e.title}` : e.title;
    return {
      id: e.id,
      title,
      start: e.start,
      end: e.end,
      extendedProps: { status: e.status ?? 'scheduled', patientName },
    };
  });

  useEffect(() => {
    if (typeof window !== 'undefined' && calRef.current) {
      const api = calRef.current.getApi();
      if (api) {
        (window as unknown as Record<string, unknown>)['__fc'] = api;
      }
    }
  });

  return (
    <div className="flex flex-col gap-4 p-6">
      <PageHeader
        title="Schedule"
        description={getWeekRange()}
        actions={
          <>
            <Button
              variant="outline"
              onClick={() => {
                const api = calRef.current?.getApi();
                api?.today();
              }}
            >
              Today
            </Button>
            <Button
              onClick={() => {
                const now = new Date();
                const end = new Date(now.getTime() + 30 * 60 * 1000);
                setNewApptRange({ start: now.toISOString(), end: end.toISOString() });
              }}
            >
              + New appointment
            </Button>
          </>
        }
      />

      {/* Toolbar Card */}
      <Card>
        <CardContent className="flex items-center gap-3 py-3">
          {/* Provider filter */}
          <Select value={providerFilter} onValueChange={setProviderFilter}>
            <SelectTrigger className="w-44" data-testid="provider-filter">
              <SelectValue placeholder="All providers" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All providers</SelectItem>
              {doctors.map((d) => (
                <SelectItem key={d.id} value={String(d.id)}>
                  {d.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Service filter */}
          <Select value={serviceFilter} onValueChange={setServiceFilter}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder="All services" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All services</SelectItem>
              {services.map((s) => (
                <SelectItem key={s.id} value={String(s.id)}>
                  {s.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Status legend */}
          <div className="flex items-center gap-1.5">
            {Object.entries(STATUS_COLORS).map(([status, cls]) => (
              <Badge key={status} className={`text-xs capitalize ${cls}`} variant="outline">
                {status}
              </Badge>
            ))}
          </div>

          {/* View toggle — pushed to the right */}
          <div className="ml-auto">
            <Tabs value={activeView} onValueChange={(v) => handleViewChange(v as 'Day' | 'Week' | 'Month')}>
              <TabsList>
                <TabsTrigger value="Day">Day</TabsTrigger>
                <TabsTrigger value="Week">Week</TabsTrigger>
                <TabsTrigger value="Month">Month</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardContent>
      </Card>

      {/* Calendar Card */}
      <Card>
        <CardContent className="p-0">
          <FullCalendar
            ref={calRef}
            plugins={[timeGridPlugin, dayGridPlugin, interactionPlugin]}
            initialView="timeGridWeek"
            headerToolbar={false}
            slotDuration="00:15:00"
            selectable
            editable
            events={fcEvents}
            select={handleSelect}
            eventClick={handleEventClick}
            eventDrop={handleEventDrop}
            eventDidMount={(info) => {
              const status = info.event.extendedProps?.status as string | undefined;
              if (status) {
                info.el.setAttribute('data-status', status.toLowerCase().replace('_', ''));
              }
              const patientName = info.event.extendedProps?.patientName as string | undefined;
              const service = info.event.title;
              if (patientName) {
                info.el.setAttribute('title', `${patientName} · ${service} · ${status ?? ''}`);
              }
            }}
          />
        </CardContent>
      </Card>

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
    </div>
  );
}
