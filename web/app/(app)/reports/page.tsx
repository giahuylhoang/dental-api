'use client';

import { useEffect, useState } from 'react';
import { fetcher } from '@/lib/api/client';
import { KpiTile } from '@/components/dental/KpiTile';
import { LockedFeature } from '@/components/dental/LockedFeature';
import styles from './page.module.css';

// TODO: wire to dental-agent — endpoint not yet implemented
const SPARKLINE_DATA = [42800,45200,41600,48900,52100,49300,55400,51800,58200,54600,61300,63800];
const maxSpark = Math.max(...SPARKLINE_DATA);
const sparkPoints = SPARKLINE_DATA.map((v, i) => `${(i / (SPARKLINE_DATA.length - 1)) * 280},${60 - (v / maxSpark) * 55}`).join(' ');

// TODO: wire to dental-agent — endpoint not yet implemented
const AGING = [
  { label: 'Current',    amount: '$12,840', pct: 100, cls: '' },
  { label: '1–30 days',  amount: '$4,210',  pct: 33,  cls: '' },
  { label: '31–60 days', amount: '$2,180',  pct: 17,  cls: 'warn' },
  { label: '61–90 days', amount: '$890',    pct: 7,   cls: 'warn' },
  { label: '90+ days',   amount: '$340',    pct: 3,   cls: 'danger' },
];

// TODO: wire to dental-agent — endpoint not yet implemented
const PROVIDERS = [
  { name: 'Dr. Hau Le',    hrs_booked: 38, hrs_billed: 36, rate: '$312' },
  { name: 'Dr. Sara Osei', hrs_booked: 32, hrs_billed: 31, rate: '$298' },
  { name: 'Dr. Raj Patel', hrs_booked: 28, hrs_billed: 26, rate: '$274' },
];

// TODO: wire to dental-agent — endpoint not yet implemented
const TOP_PROCS = [
  { code: '11101', desc: 'Periodic oral exam',      count: 84,  avg: '$65' },
  { code: '21211', desc: 'Amalgam restoration 1S',  count: 42,  avg: '$148' },
  { code: '43101', desc: 'Scaling per unit',        count: 210, avg: '$22' },
  { code: '52101', desc: 'Acrylic denture — upper', count: 8,   avg: '$1,240' },
];

// TODO: wire to dental-agent — endpoint not yet implemented
const RECALL = [
  { rule: '6-month recall',  due: 24, conv: '71%' },
  { rule: '3-month perio',   due: 9,  conv: '55%' },
  { rule: 'Post-treatment',  due: 6,  conv: '83%' },
];

export default function ReportsPage() {
  const [kpi, setKpi] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    fetcher<Record<string, number>>('/api/v2/reporting/kpi').then(setKpi).catch(() => {});
  }, []);

  return (
    <div className={styles.body}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Reports</h1>
          <p className={styles.pageSub}>Operational and clinical KPIs</p>
        </div>
      </div>

      <div className={styles.kpiRow}>
        <KpiTile label="Revenue (30d)"       value={kpi ? `$${kpi.production_this_month?.toLocaleString() ?? '63,800'}` : '$63,800'} delta="+8.4% vs prev 30d" trend="up" />
        <KpiTile label="AR Outstanding"      value="$20,460" delta="-3.1% vs prev 30d" trend="down" />
        <KpiTile label="Recall conversion"   value="71%"     delta="+2pp"              trend="up" />
        <KpiTile label="New patients (30d)"  value="18"      delta="+3 vs prev 30d"    trend="up" />
        <KpiTile label="Avg booking lead"    value="3.2d"    delta="-0.4d"             trend="down" />
      </div>

      <div className={styles.grid2}>
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <div className={styles.panelHTitle}>Revenue trend</div>
              <div className={styles.panelHSub}>12-week rolling</div>
            </div>
          </div>
          <svg viewBox="0 0 280 64" style={{ width: '100%', height: 80 }}>
            <polyline points={sparkPoints} fill="none" stroke="var(--rr-steel-500)" strokeWidth="2" strokeLinejoin="round" />
            <polyline points={`0,64 ${sparkPoints} 280,64`} fill="rgba(58,127,189,0.08)" stroke="none" />
          </svg>
        </div>
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <div>
              <div className={styles.panelHTitle}>AR Aging</div>
              <div className={styles.panelHSub}>Outstanding by age bucket</div>
            </div>
          </div>
          <div className={styles.agingGrid}>
            {AGING.map(a => (
              <div key={a.label} className={`${styles.agingCell} ${a.cls === 'warn' ? styles.warn : a.cls === 'danger' ? styles.danger : ''}`}>
                <div className={styles.agingLabel}>{a.label}</div>
                <div className={styles.agingAmount}>{a.amount}</div>
                <div className={styles.agingBarTrack}><div className={styles.agingBarFill} style={{ width: `${a.pct}%` }} /></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.grid2}>
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <div><div className={styles.panelHTitle}>Provider productivity</div></div>
          </div>
          <table className={styles.list}>
            <thead><tr><th>Provider</th><th>Hrs booked</th><th>Hrs billed</th><th>$/hr</th></tr></thead>
            <tbody>
              {PROVIDERS.map(p => (
                <tr key={p.name}>
                  <td>{p.name}</td>
                  <td className={styles.num}>{p.hrs_booked}</td>
                  <td className={styles.num}>{p.hrs_billed}</td>
                  <td className={styles.num}>{p.rate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <div><div className={styles.panelHTitle}>Top procedures</div></div>
          </div>
          <table className={styles.list}>
            <thead><tr><th>Code</th><th>Description</th><th>Count</th><th>Avg fee</th></tr></thead>
            <tbody>
              {TOP_PROCS.map(p => (
                <tr key={p.code}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '.76rem' }}>{p.code}</td>
                  <td>{p.desc}</td>
                  <td className={styles.num}>{p.count}</td>
                  <td className={styles.num}>{p.avg}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <div><div className={styles.panelHTitle}>Recall queue summary</div></div>
        </div>
        <table className={styles.list}>
          <thead><tr><th>Rule</th><th>Due this week</th><th>Conversion %</th></tr></thead>
          <tbody>
            {RECALL.map(r => (
              <tr key={r.rule}>
                <td>{r.rule}</td>
                <td className={styles.num}>{r.due}</td>
                <td className={styles.num}>{r.conv}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <LockedFeature
        title="Advanced reports"
        body="Custom queries and CSV export are paused while we rebuild the export pipeline."
        backHref="/dashboard"
      />
    </div>
  );
}
