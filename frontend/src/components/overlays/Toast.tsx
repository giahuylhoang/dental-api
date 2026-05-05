'use client';

import React from 'react';
import { CheckCircle, X } from 'lucide-react';

interface ToastItem {
  id: number;
  msg: string;
  detail?: string;
}

interface ToastContainerProps {
  toasts: ToastItem[];
  onDismiss: (id: number) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="toast-stack">
      {toasts.map(t => (
        <div key={t.id} className="toast success">
          <CheckCircle size={20} strokeWidth={1.5} className="toast-ico" />
          <div className="toast-body">
            {t.msg}
            {t.detail && <span className="toast-detail">{t.detail}</span>}
          </div>
          <button className="toast-x" onClick={() => onDismiss(t.id)}><X size={14} /></button>
        </div>
      ))}
    </div>
  );
}

// Hook for toast management
export function useToast() {
  const [toasts, setToasts] = React.useState<ToastItem[]>([]);

  const addToast = (msg: string, detail?: string) => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, detail }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  };

  const dismissToast = (id: number) => setToasts(t => t.filter(x => x.id !== id));

  return { toasts, addToast, dismissToast };
}
