'use client';

import React from 'react';
import Link from 'next/link';

const LOGIN_WORDS = ['Schedules.', 'Charts.', 'Plans.', 'Practices.'];

export default function LoginPage() {
  const [wordIdx, setWordIdx] = React.useState(0);
  const [visible, setVisible] = React.useState(true);
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => { setWordIdx(i => (i + 1) % LOGIN_WORDS.length); setVisible(true); }, 380);
    }, 2800);
    return () => clearInterval(id);
  }, []);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length >= 6) {
      window.location.href = '/dashboard';
    } else {
      setError('Password must be at least 6 characters.');
    }
  };

  const inputStyle: React.CSSProperties = {
    fontFamily: "'Inter', sans-serif", fontSize: '0.92rem', color: '#FAF9F6',
    background: 'rgba(255,255,255,0.04)', border: '1.5px solid rgba(255,255,255,0.12)',
    borderRadius: 6, padding: '12px 14px', outline: 'none', width: '100%',
    transition: 'border-color 200ms ease, box-shadow 200ms ease',
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.05fr 1fr', minHeight: '100vh', position: 'relative', overflow: 'hidden', background: '#060F1E' }}>
      {/* Left copy */}
      <div style={{ padding: '60px 56px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', position: 'relative', zIndex: 2 }}>
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 12, textDecoration: 'none' }}>
          <img src="/assets/RR_logo_white.svg" alt="RR" style={{ height: 32 }} />
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.05 }}>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: '.95rem', letterSpacing: '.08em', textTransform: 'uppercase', color: '#FAF9F6' }}>ROCKYRIDGE</span>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 400, fontSize: '.82rem', letterSpacing: '1.8px', color: 'rgba(250,249,246,0.7)', textTransform: 'uppercase' }}>DENTAL AI</span>
          </div>
        </Link>

        <div style={{ maxWidth: 540 }}>
          <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '.72rem', letterSpacing: '.15em', textTransform: 'uppercase', color: '#6BAED6', marginBottom: 24 }}>
            Sign in to your workspace · Sovereign · Audit-logged
          </div>
          <h1 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 900, fontSize: 'clamp(2.2rem, 4.5vw, 3.6rem)', lineHeight: 1.08, letterSpacing: '-.03em', color: '#FAF9F6', margin: 0 }}>
            Architecting<br />Sovereign{' '}
            <span style={{
              display: 'inline-block', color: '#6BAED6', minWidth: '4ch',
              opacity: visible ? 1 : 0,
              transform: visible ? 'translateY(0)' : 'translateY(10px)',
              transition: 'opacity 320ms cubic-bezier(0.16,1,0.3,1), transform 320ms cubic-bezier(0.16,1,0.3,1)',
            }}>{LOGIN_WORDS[wordIdx]}</span>
          </h1>
          <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '1rem', lineHeight: 1.75, color: 'rgba(250,249,246,0.6)', marginTop: 22, maxWidth: 460 }}>
            Open the schedule. Open the chart. Open the lab. The history is already there — patient context, recall windows, lab ETAs, insurance status, all in one connected system.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 36, paddingTop: 32, borderTop: '1px solid rgba(255,255,255,0.09)', flexWrap: 'wrap' }}>
          {[['Sovereign', 'Your data, your tenancy'], ['Audit-logged', 'Every clinical edit, every login'], ['Light-on-the-eyes', '8-hour shift-friendly']].map(([k, v]) => (
            <div key={k}>
              <div style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1rem', color: '#FAF9F6', letterSpacing: '-.01em' }}>{k}</div>
              <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '.72rem', color: 'rgba(250,249,246,0.4)', marginTop: 3, letterSpacing: '.03em' }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right side — pillar labels + rules */}
      <div style={{ position: 'relative', height: '100vh' }}>
        {[['THE SCHEDULE', '14%'], ['THE CHART', '47%'], ['THE LAB', '76%']].map(([lbl, top]) => (
          <div key={lbl} style={{
            position: 'absolute', left: 8, top, fontFamily: "'Inter', sans-serif",
            fontWeight: 700, fontSize: '.6rem', letterSpacing: '.14em', textTransform: 'uppercase',
            color: 'rgba(58,127,189,0.35)', writingMode: 'vertical-rl',
            transform: 'rotate(180deg)', userSelect: 'none',
          }}>{lbl}</div>
        ))}
        {['33.3%', '66.6%'].map(top => (
          <div key={top} style={{ position: 'absolute', left: 32, right: 0, top, height: 1, background: 'rgba(58,127,189,0.07)' }} />
        ))}

        {/* Login card */}
        <div style={{ position: 'absolute', right: 56, top: '50%', transform: 'translateY(-50%)', zIndex: 3 }}>
          <form id="login-form" onSubmit={handleLogin} style={{
            background: 'rgba(13,33,55,0.85)', backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
            padding: 36, width: 380, boxShadow: '0 16px 60px rgba(10,25,47,0.55)',
            display: 'flex', flexDirection: 'column', gap: 18,
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.15em', textTransform: 'uppercase', color: '#6BAED6' }}>Sign in</div>
              <h2 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: '1.6rem', color: '#FAF9F6', margin: 0, letterSpacing: '-0.02em' }}>Welcome back</h2>
              <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.82rem', color: 'rgba(250,249,246,0.6)', margin: 0, lineHeight: 1.6 }}>
                Sign in to your clinic. Sessions are audit-logged and expire after 12 h of inactivity.
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.74rem', fontWeight: 600, color: 'rgba(250,249,246,0.85)' }}>Email</label>
              <input id="login-email" name="email" style={inputStyle} placeholder="hau@oakdentalcalgary.com" value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <label style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.74rem', fontWeight: 600, color: 'rgba(250,249,246,0.85)' }}>Password</label>
                <a href="#" style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.72rem', color: '#6BAED6', textDecoration: 'none' }}>Forgot?</a>
              </div>
              <input id="login-password" name="password" style={inputStyle} type="password" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} />
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: "'Inter', sans-serif", fontSize: '0.78rem', color: 'rgba(250,249,246,0.6)' }}>
              <input type="checkbox" style={{ accentColor: '#3A7FBD' }} /> Remember this device for 30 days
            </label>
            <button type="submit" className="btn btn-white btn-lg" style={{ width: '100%', justifyContent: 'center' }}>Sign in</button>
            {error && <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.78rem', color: '#F87171' }}>{error}</div>}
            <div style={{ textAlign: 'center', fontFamily: "'Inter', sans-serif", fontSize: '0.72rem', color: 'rgba(250,249,246,0.4)' }}>
              Need access? <Link href="/#contact" style={{ color: '#6BAED6', textDecoration: 'none' }}>Contact your clinic admin →</Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
