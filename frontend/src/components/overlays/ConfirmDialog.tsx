'use client';

import React from 'react';
import { CenterModal } from '@/components/overlays/CenterModal';

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  body: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  body,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  destructive,
}: ConfirmDialogProps) {
  const [busy, setBusy] = React.useState(false);

  const handleConfirm = async () => {
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
    }
  };

  return (
    <CenterModal open={open} onClose={busy ? () => undefined : onClose} width="min(440px, 92vw)">
      <div className="center-modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <div className="appt-ws-name" style={{ marginBottom: 6 }}>{title}</div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: '.86rem', color: 'var(--rr-slate-dark)', lineHeight: 1.45 }}>
            {body}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button
            className="btn btn-ghost btn-md"
            onClick={onClose}
            disabled={busy}
            type="button"
          >
            {cancelLabel}
          </button>
          <button
            className={'btn btn-md ' + (destructive ? 'btn-destructive' : 'btn-primary')}
            onClick={handleConfirm}
            disabled={busy}
            type="button"
          >
            {busy ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </CenterModal>
  );
}
