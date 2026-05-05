'use client';

import React from 'react';
import { KpiTile } from '@/components/domain/KpiTile';
import { APPOINTMENTS, INVOICES } from '@/lib/data';
import { api } from '@/lib/api';
import { useToast } from '@/components/overlays/ToastContext';

export default function ReportsPage() {
  const { addToast } = useToast();
  const totalRevenue = INVOICES.reduce((s, i) => s + i.total, 0);
  const outstanding = INVOICES.reduce((s, i) => s + i.balance, 0);

  const handleExportCSV = async () => {
    try {
      const kpi = await api.v2.reporting.kpi();
      // In a real app, this would generate a CSV file
      addToast('CSV exported.', 'reports.csv');
    } catch { addToast('Failed to export CSV.'); }
  };
  
  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <div className="page-sub">Practice analytics · Last 30 days</div>
        </div>
        <button className="btn btn-ghost btn-md" onClick={handleExportCSV}>Export CSV</button>
      </div>
      <div className="kpi-row">
        <KpiTile label="Total Revenue" value={`$${(totalRevenue / 1000).toFixed(1)}K`} delta="+ 8.2%" trend="up" accent="steel" />
        <KpiTile label="Appointments" value={String(APPOINTMENTS.length * 4)} delta="+ 12%" trend="up" accent="steel" />
        <KpiTile label="No-show Rate" value="4.2%" delta="+ 0.3%" trend="down" accent="navy" />
        <KpiTile label="Collection Rate" value="84%" delta="+ 1.5%" trend="up" accent="steel" />
      </div>
      <div className="panel">
        <div className="panel-header">
          <div className="panel-h-title">Revenue Breakdown</div>
          <div className="panel-h-sub">By procedure category</div>
        </div>
        {[{ label: 'Crown & Bridge', pct: 42, amt: 6120 }, { label: 'Hygiene & Recall', pct: 28, amt: 4080 }, { label: 'Denture', pct: 18, amt: 2620 }, { label: 'Consult & Exam', pct: 12, amt: 1750 }].map(r => (
          <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '10px 0', borderBottom: '1px solid #EDE9E0' }}>
            <div style={{ flex: 1, fontFamily: "'Inter', sans-serif", fontSize: '.88rem', color: '#1C2333' }}>{r.label}</div>
            <div style={{ background: '#F5F2EC', borderRadius: 4, height: 8, width: 200, overflow: 'hidden' }}>
              <div style={{ background: '#3A7FBD', height: '100%', width: `${r.pct}%`, borderRadius: 4 }} />
            </div>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.82rem', color: '#4A5568', width: 80, textAlign: 'right' }}>${r.amt.toLocaleString()}</span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '.78rem', color: '#8A9BB0', width: 40, textAlign: 'right' }}>{r.pct}%</span>
          </div>
        ))}
      </div>
    </>
  );
}
