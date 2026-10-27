import { type Incident, violationLabel } from "../api";

interface Props {
  toasts: Incident[];
  onDismiss: (id: number) => void;
}

export function AlertToasts({ toasts, onDismiss }: Props) {
  return (
    <div className="toasts" role="status" aria-live="assertive">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.severity}`}>
          <div>
            <strong>{violationLabel(t.type)}</strong>
            <div className="muted">
              {t.camera_name} · {t.zone} · {new Date(t.created_at).toLocaleTimeString()}
            </div>
          </div>
          <button className="icon-btn" onClick={() => onDismiss(t.id)} aria-label="Dismiss">
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
