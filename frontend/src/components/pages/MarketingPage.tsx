'use client';

import React from 'react';
import { Nav } from '@/components/layout/Nav';

export function MarketingPage() {
  return (
    <>
      <Nav dark={true} />
      <section id="hero" style={{
        background: '#0A192F', minHeight: '100vh',
        display: 'grid', gridTemplateColumns: '1fr 1fr',
        alignItems: 'center', padding: '100px 0 60px',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ padding: '0 48px 0 calc(max(48px, (100% - 1200px) / 2 + 48px))', maxWidth: 660 }}>
          <div style={{
            fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem',
            letterSpacing: '0.15em', textTransform: 'uppercase', color: '#3A7FBD', marginBottom: 24,
          }}>
            Rockyridge Dental AI · Systems Thinking for Practice Operations
          </div>
          <h1 style={{
            fontFamily: "'Montserrat', sans-serif", fontWeight: 900,
            fontSize: 'clamp(2.4rem,4.5vw,4rem)', lineHeight: 1.08,
            letterSpacing: '-0.03em', color: '#FAF9F6', margin: 0,
          }}>
            Architecting<br />Sovereign Clinical Systems.
          </h1>
          <p style={{
            fontFamily: "'Inter', sans-serif", fontSize: '1.05rem', lineHeight: 1.8,
            color: 'rgba(250,249,246,0.6)', marginTop: 24, maxWidth: 480,
          }}>
            The dental practice OS for clinics that want their schedule, their charts,
            their lab cases, and their insurance reconciliation — all in one place, owned by the clinic.
          </p>
          <div style={{ display: 'flex', gap: 16, marginTop: 40, flexWrap: 'wrap', alignItems: 'center' }}>
            <a href="/#contact" className="btn btn-white btn-lg" style={{ textDecoration: 'none' }}>Schedule a demo</a>
            <a href="/login" className="btn btn-white btn-lg" style={{ opacity: 0.6, textDecoration: 'none' }}>Sign in</a>
          </div>
          <div style={{ display: 'flex', gap: 40, marginTop: 60, paddingTop: 36, borderTop: '1px solid rgba(255,255,255,0.09)', flexWrap: 'wrap' }}>
            {[['Three Pillars','Schedule · Chart · Lab'], ['Sovereign','Your data, your servers'], ['Audit-logged','Always · forever']].map(([s, d]) => (
              <div key={s}>
                <div style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1rem', color: '#FAF9F6', letterSpacing: '-0.01em' }}>{s}</div>
                <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.75rem', color: 'rgba(250,249,246,0.4)', marginTop: 3, letterSpacing: '0.03em' }}>{d}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ height: '100vh', position: 'relative', opacity: 0.9 }}>
          {[['THE SCHEDULE', '14%'], ['THE CHART', '47%'], ['THE LAB', '76%']].map(([lbl, top]) => (
            <div key={lbl} style={{
              position: 'absolute', left: 8, top, fontFamily: "'Inter', sans-serif",
              fontWeight: 700, fontSize: '0.6rem', letterSpacing: '0.14em',
              textTransform: 'uppercase', color: 'rgba(58,127,189,0.35)',
              writingMode: 'vertical-rl', transform: 'rotate(180deg)', userSelect: 'none',
            }}>{lbl}</div>
          ))}
          {['33.3%', '66.6%'].map(top => (
            <div key={top} style={{ position: 'absolute', left: 32, right: 0, top, height: 1, background: 'rgba(58,127,189,0.07)' }} />
          ))}
        </div>
      </section>

      <section id="chart" style={{ background: '#FAF9F6', padding: '80px 48px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 60 }}>
            <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#3A7FBD', marginBottom: 16 }}>Three Pillars</div>
            <h2 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: 'clamp(1.8rem,3.5vw,2.8rem)', color: '#0A192F' }}>One system. Three surfaces.</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 28 }}>
            {[
              { title: 'The Schedule', desc: 'Book, confirm, check in, reschedule, and recall — all from a single day view. No double-booking. No lost slots.' },
              { title: 'The Chart', desc: 'Demographic, periograms, treatment history, insurance, tooth chart — one unified record per patient.' },
              { title: 'The Lab', desc: 'Track every case from impression to seat. Vendor, ETA, turnaround — visible at a glance.' },
            ].map(p => (
              <div key={p.title} style={{ background: '#fff', border: '1px solid #EDE9E0', borderRadius: 6, padding: 32, boxShadow: '0 1px 2px rgba(10,25,47,0.06)', display: 'flex', flexDirection: 'column', gap: 14 }}>
                <h4 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontSize: '1.2rem', color: '#0A192F' }}>{p.title}</h4>
                <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.9rem', color: '#4A5568', lineHeight: 1.7 }}>{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="lab" style={{ background: '#fff', padding: '80px 48px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ maxWidth: 720 }}>
            <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#3A7FBD', marginBottom: 16 }}>Philosophy</div>
            <blockquote style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 700, fontStyle: 'italic', fontSize: 'clamp(1.4rem,2.5vw,2rem)', color: '#1C2333', borderLeft: '3px solid #3A7FBD', paddingLeft: 32, margin: '0 0 24px', lineHeight: 1.4 }}>
              Your patient roster is either a liability or a competitive edge. The difference is the system.
            </blockquote>
            <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '1rem', color: '#4A5568', lineHeight: 1.8 }}>
              Rockyridge Dental AI doesn&apos;t replace your clinical judgment. It replaces the clipboard, the whiteboard, the filing cabinet, and the dozen browser tabs you keep open to run a day. One sovereign system. One source of truth.
            </p>
          </div>
        </div>
      </section>

      <section id="contact" style={{ background: '#0A192F', padding: '80px 48px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', textAlign: 'center' }}>
          <div style={{ fontFamily: "'Inter', sans-serif", fontWeight: 600, fontSize: '0.72rem', letterSpacing: '0.15em', textTransform: 'uppercase', color: '#6BAED6', marginBottom: 16 }}>Schedule a demo</div>
          <h2 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: 'clamp(1.8rem,3.5vw,2.8rem)', color: '#FAF9F6', marginBottom: 16 }}>See the system in action.</h2>
          <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '1.05rem', color: 'rgba(250,249,246,0.6)', maxWidth: 520, margin: '0 auto 32px' }}>
            We&apos;ll walk you through a live clinic — schedule, chart, lab pipeline, insurance reconciliation — on your own data model.
          </p>
          <a href="/#contact" className="btn btn-white btn-lg" style={{ textDecoration: 'none' }}>Schedule a demo</a>
        </div>
      </section>

      <footer style={{ background: '#060F1E', padding: '32px 48px', textAlign: 'center' }}>
        <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.75rem', color: 'rgba(250,249,246,0.3)', letterSpacing: '0.06em' }}>
          ROCKYRIDGE · DENTAL AI · v1 · Sovereign Clinical Systems
        </div>
      </footer>
    </>
  );
}
