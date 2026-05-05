'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, X } from 'lucide-react';

interface ToastItem {
  id: number;
  msg: string;
  detail?: string;
}

interface ToastContextType {
  addToast: (msg: string, detail?: string) => void;
  dismissToast: (id: number) => void;
}

const ToastContext = createContext<ToastContextType>({ addToast: () => {}, dismissToast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((msg: string, detail?: string) => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, detail }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts(t => t.filter(x => x.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, dismissToast }}>
      {children}
      {toasts.length > 0 && (
        <div className="toast-stack">
          {toasts.map(t => (
            <div key={t.id} className="toast success">
              <CheckCircle size={20} strokeWidth={1.5} className="toast-ico" />
              <div className="toast-body">
                {t.msg}
                {t.detail && <span className="toast-detail">{t.detail}</span>}
              </div>
              <button className="toast-x" onClick={() => dismissToast(t.id)}><X size={14} /></button>
            </div>
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}
