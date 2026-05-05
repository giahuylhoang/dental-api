'use client';

import React from 'react';
import { X, ArrowLeft } from 'lucide-react';

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  meta?: string;
  title: string;
  sub?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  showBack?: boolean;
}

export function Drawer({ open, onClose, meta, title, sub, children, footer, showBack }: DrawerProps) {
  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    if (open) document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <aside className="drawer" role="dialog">
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'flex-start' }}>
            {showBack && (
              <button className="drawer-back" onClick={onClose}>
                <ArrowLeft size={18} strokeWidth={1.5} />
              </button>
            )}
            <div>
              {meta && <div className="drawer-meta">{meta}</div>}
              <div className="drawer-title">{title}</div>
              {sub && <div className="drawer-sub">{sub}</div>}
            </div>
          </div>
          <button className="drawer-x" onClick={onClose}><X size={18} /></button>
        </div>
        <div className="drawer-body">
          {children}
        </div>
        {footer && (
          <div className="drawer-footer">
            {footer}
          </div>
        )}
      </aside>
    </>
  );
}
