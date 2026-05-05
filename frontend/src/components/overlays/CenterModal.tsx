'use client';

import React from 'react';
import { ArrowLeft } from 'lucide-react';

interface CenterModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  width?: string;
  children: React.ReactNode;
}

export function CenterModal({ open, onClose, width, children }: CenterModalProps) {
  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    if (open) document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="center-modal-backdrop" onClick={onClose}>
      <div className="center-modal" style={width ? { width } : undefined} onClick={e => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}
