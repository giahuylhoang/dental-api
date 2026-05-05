import { NOTIFICATIONS } from '@/lib/data';

interface NotificationsDropdownProps {
  onClose: () => void;
}

export function NotificationsDropdown({ onClose }: NotificationsDropdownProps) {
  return (
    <>
      <div className="dd-overlay" onClick={onClose} />
      <div className="dd-menu" style={{ top: 58, right: 80, minWidth: 340 }}>
        <div className="dd-head">
          <div className="dd-name">Notifications</div>
          <div className="dd-sub">{NOTIFICATIONS.filter(n => !n.read).length} unread</div>
        </div>
        <div className="dd-sep" />
        {NOTIFICATIONS.map(n => (
          <div key={n.id} className="notif-item" onClick={onClose}>
            <span className={'notif-dot' + (n.read ? ' read' : '')} />
            <div>
              <div className="notif-text">{n.text}</div>
              <div className="notif-time">{n.time}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
