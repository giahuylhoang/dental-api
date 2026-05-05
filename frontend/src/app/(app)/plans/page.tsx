import React from 'react';
import { Check } from 'lucide-react';

const PLANS = [
  { name: 'Starter', price: '$149', period: '/month', features: ['3 providers', 'Unlimited patients', 'Appointment booking', 'Basic reporting', 'Email support'] },
  { name: 'Professional', price: '$349', period: '/month', features: ['10 providers', 'Unlimited patients', 'Full schedule + lab', 'Insurance reconciliation', 'Recall automation', 'Priority support', 'API access'], highlight: true },
  { name: 'Enterprise', price: 'Custom', period: '', features: ['Unlimited providers', 'Multi-clinic support', 'Dedicated tenant', 'Custom integrations', 'SLA + uptime guarantee', 'Training + onboarding'] },
];

export default function PlansPage() {
  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Plans</h1>
          <div className="page-sub">Choose the right plan for your practice</div>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
        {PLANS.map(p => (
          <div key={p.name} className="panel" style={{
            borderColor: p.highlight ? '#3A7FBD' : '#EDE9E0',
            borderWidth: p.highlight ? 2 : 1,
            position: 'relative',
          }}>
            {p.highlight && (
              <div style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', background: '#3A7FBD', color: '#fff', padding: '4px 16px', borderRadius: 999, fontFamily: "'Inter', sans-serif", fontSize: '.68rem', fontWeight: 600, letterSpacing: '.08em', textTransform: 'uppercase' }}>Most popular</div>
            )}
            <div style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1.3rem', color: '#0A192F', marginBottom: 4 }}>{p.name}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, marginBottom: 20 }}>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '2.2rem', fontWeight: 700, color: '#0A192F' }}>{p.price}</span>
              <span style={{ fontFamily: "'Inter', sans-serif", fontSize: '.9rem', color: '#4A5568' }}>{p.period}</span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 20px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {p.features.map(f => (
                <li key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: "'Inter', sans-serif", fontSize: '.88rem', color: '#1C2333' }}>
                  <Check size={16} strokeWidth={2} color="#2A7D4F" /> {f}
                </li>
              ))}
            </ul>
            <button data-audit="local-only" className={`btn ${p.highlight ? 'btn-primary' : 'btn-ghost'} btn-md`} style={{ width: '100%', justifyContent: 'center' }}>{p.price === 'Custom' ? 'Contact us' : 'Start trial'}</button>
          </div>
        ))}
      </div>
    </>
  );
}
