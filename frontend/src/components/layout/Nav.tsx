'use client';

import React from 'react';
import Link from 'next/link';

interface NavProps {
  currentSection?: string;
  onNav?: (section: string) => void;
  dark?: boolean;
}

export function Nav({ currentSection, onNav, dark = true }: NavProps) {
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const links = [
    { label: 'Schedule', anchor: 'schedule' },
    { label: 'Chart', anchor: 'chart' },
    { label: 'Lab', anchor: 'lab' },
    { label: 'Pricing', anchor: 'pricing' },
    { label: 'Contact', anchor: 'contact' },
  ];

  const tone = dark
    ? {
        bg: scrolled ? 'rgba(10,25,47,0.92)' : 'transparent',
        link: 'rgba(250,249,246,0.72)',
        linkActive: '#FAF9F6',
        brand: '#FAF9F6',
        sub: 'rgba(250,249,246,0.7)',
        logo: '/assets/RR_logo_white.svg',
        cta: 'btn-white' as const,
      }
    : {
        bg: scrolled ? 'rgba(255,255,255,0.92)' : 'transparent',
        link: '#3D4D61',
        linkActive: '#0A192F',
        brand: '#0A192F',
        sub: '#4A5568',
        logo: '/assets/RR_logo_blue.svg',
        cta: 'btn-navy' as const,
      };

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
      background: tone.bg,
      backdropFilter: scrolled ? 'blur(12px)' : 'none',
      borderBottom: scrolled ? '1px solid rgba(255,255,255,0.08)' : 'none',
      transition: 'all 250ms cubic-bezier(0.16,1,0.3,1)',
      padding: '0 48px',
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', height: 72, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Link href="/#hero" style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12, padding: 0, textDecoration: 'none' }}>
          <img src={tone.logo} alt="Rockyridge Dental AI" style={{ height: 36, width: 'auto' }} />
          <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.05, textAlign: 'left' }}>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: 18, color: tone.brand, letterSpacing: '0.08em', textTransform: 'uppercase' }}>ROCKYRIDGE</span>
            <span style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 400, fontSize: 14, color: tone.sub, letterSpacing: 2.1 }}>DENTAL AI</span>
          </div>
        </Link>

        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          {links.map(l => {
            const active = currentSection === l.anchor;
            return (
              <a
                key={l.label}
                href={`/#${l.anchor}`}
                onClick={onNav ? (e) => { e.preventDefault(); onNav(l.anchor); } : undefined}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.875rem',
                  color: active ? tone.linkActive : tone.link,
                  letterSpacing: '0.01em', padding: '2px 0',
                  position: 'relative', transition: 'color 200ms ease',
                  textDecoration: 'none', display: 'inline-block',
                }}
              >
                {l.label}
                <span style={{
                  position: 'absolute', bottom: -1, left: 0, right: 0, height: 1.5,
                  background: tone.linkActive,
                  transform: active ? 'scaleX(1)' : 'scaleX(0)',
                  transformOrigin: 'left',
                  transition: 'transform 280ms cubic-bezier(0.16,1,0.3,1)',
                  pointerEvents: 'none',
                }} />
              </a>
            );
          })}
          <Link href="/login" style={{ fontFamily: "'Inter', sans-serif", fontWeight: 500, fontSize: '0.875rem', color: tone.link, textDecoration: 'none' }}>Sign in</Link>
          <Link href="/#contact" className={`btn ${tone.cta} btn-md`} style={{ textDecoration: 'none' }}>
            Schedule a demo
          </Link>
        </div>
      </div>
    </nav>
  );
}
