import { useCallback, useEffect, useState } from "react";
import { api, type Incident } from "./api";
import { playAlarm } from "./alarm";
import { AlertToasts } from "./components/AlertToasts";
import { AlertsLog } from "./pages/AlertsLog";
import { LiveMonitoring } from "./pages/LiveMonitoring";
import { useAlertsSocket } from "./useAlertsSocket";

type Page = "live" | "alerts";
const TOAST_MS = 8000;

export default function App() {
  const [page, setPage] = useState<Page>("live");
  const [latest, setLatest] = useState<Incident[]>([]);
  const [toasts, setToasts] = useState<Incident[]>([]);
  const [unseen, setUnseen] = useState(0);

  useEffect(() => {
    api.incidents({ limit: 50 }).then((res) => setLatest(res.items)).catch(() => {});
  }, []);

  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);

  useAlertsSocket((incident) => {
    setLatest((list) => [incident, ...list].slice(0, 50));
    setToasts((t) => [incident, ...t].slice(0, 4));
    window.setTimeout(() => dismiss(incident.id), TOAST_MS);
    if (page !== "alerts") setUnseen((n) => n + 1);
    playAlarm(incident.severity === "critical" || incident.severity === "high");
  });

  const open = (next: Page) => {
    setPage(next);
    if (next === "alerts") setUnseen(0);
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden>◆</span> Smart-EHS
        </div>
        <nav className="tabs">
          <button className={page === "live" ? "tab active" : "tab"} onClick={() => open("live")}>
            Live monitoring
          </button>
          <button className={page === "alerts" ? "tab active" : "tab"} onClick={() => open("alerts")}>
            Alerts log {unseen > 0 && <span className="count">{unseen}</span>}
          </button>
        </nav>
      </header>

      <main className="content">
        {page === "live" ? <LiveMonitoring latest={latest} /> : <AlertsLog refreshKey={latest[0]?.id ?? 0} />}
      </main>

      <AlertToasts toasts={toasts} onDismiss={dismiss} />
    </div>
  );
}
