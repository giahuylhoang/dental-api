'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api, AppointmentDTO } from '@/lib/api';
import { StatusPill } from '@/components/domain/StatusPill';
import { EmptyState } from '@/components/domain/EmptyState';
import { ToothChartTile } from '@/components/domain/ToothChartTile';

export default function AppointmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [appt, setAppt] = useState<AppointmentDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAppt = async () => {
    try {
      const data = await api.appointments.get(params.id as string);
      setAppt(data);
    } catch (e) {
      setError('Appointment not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAppt(); }, [params.id]);

  const handleStatus = async (status: string) => {
    if (!appt) return;
    await api.appointments.setStatus(appt.id, status);
    await fetchAppt();
  };

  const handleCancel = async () => {
    if (!appt) return;
    await api.appointments.cancel(appt.id);
    await fetchAppt();
  };

  const handleReschedule = async () => {
    if (!appt) return;
    const newStart = prompt('New start time (ISO format):', appt.start_time);
    const newEnd = prompt('New end time (ISO format):', appt.end_time);
    if (!newStart || !newEnd) return;
    await api.appointments.reschedule(appt.id, {
      start_time: newStart,
      end_time: newEnd,
      patient_id: appt.patient_id,
      provider_id: appt.provider_id,
      service_id: appt.service_id,
      reason: appt.reason_note || '',
      patient_name: appt.patient_name || '',
      service_name: appt.service_name || '',
    });
    router.push('/schedule');
  };

  if (loading) return <div>Loading...</div>;
  if (error || !appt) return <EmptyState title="Appointment not found" />;

  const initials = (appt.patient_name || 'U').split(' ').map(s => s[0]).slice(0, 2).join('').toUpperCase();

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">{appt.patient_name || 'Unknown'}</h1>
          <div className="page-sub">{appt.id} · {appt.start_time}</div>
        </div>
        <StatusPill status={appt.status} />
      </div>

      <div className="appt-ws-hero">
        <div className="appt-ws-ava">{initials}</div>
        <div className="appt-ws-info">
          <div className="appt-ws-name">{appt.patient_name || 'Unknown'}</div>
          <div className="appt-ws-detail">{appt.service_name} · Provider {appt.provider_id} · {appt.start_time}</div>
          <div className="appt-ws-id">{appt.id} · {appt.patient_id}</div>
        </div>
        <StatusPill status={appt.status} />
      </div>

      <div className="appt-ws-actions">
        <button className="btn btn-primary btn-md" onClick={() => handleStatus('confirmed')} data-testid="btn-confirm">Confirm</button>
        <button className="btn btn-ghost btn-md" onClick={() => handleStatus('checked_in')} data-testid="btn-checkin">Check in</button>
        <button className="btn btn-ghost btn-md" onClick={() => handleStatus('in_progress')} data-testid="btn-start">Start</button>
        <button className="btn btn-ghost btn-md" onClick={() => handleStatus('completed')} data-testid="btn-complete">Complete</button>
        <button className="btn btn-ghost btn-md" onClick={() => handleStatus('no_show')} data-testid="btn-noshow">No show</button>
        <button className="btn btn-ghost btn-md" onClick={handleReschedule} data-testid="btn-reschedule">Reschedule</button>
        <button className="btn btn-ghost btn-md" style={{ color: 'var(--rr-error)' }} onClick={handleCancel} data-testid="btn-cancel">Cancel</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
        <div className="panel">
          <div className="detail-row"><span className="detail-k">Appointment</span><span className="detail-v">{appt.id}</span></div>
          <div className="detail-row"><span className="detail-k">Patient</span><span className="detail-v">{appt.patient_name}</span></div>
          <div className="detail-row"><span className="detail-k">Service</span><span className="detail-v">{appt.service_name}</span></div>
          <div className="detail-row"><span className="detail-k">Provider</span><span className="detail-v">{appt.provider_id}</span></div>
          <div className="detail-row"><span className="detail-k">Time</span><span className="detail-v">{appt.start_time} - {appt.end_time}</span></div>
          <div className="detail-row"><span className="detail-k">Status</span><span className="detail-v"><StatusPill status={appt.status} /></span></div>
        </div>
        <ToothChartTile />
      </div>
    </>
  );
}
