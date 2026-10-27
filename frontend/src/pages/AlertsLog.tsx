import { useEffect, useState } from "react";
import { api, type Incident, VIOLATION_LABELS, violationLabel } from "../api";
import { SeverityBadge } from "../components/SeverityBadge";

const PAGE_SIZE = 25;

export function AlertsLog({ refreshKey }: { refreshKey: number }) {
  const [items, setItems] = useState<Incident[]>([]);
  const [total, setTotal] = useState(0);
  const [type, setType] = useState("");
  const [page, setPage] = useState(0);
  const [busy, setBusy] = useState<number>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    api
      .incidents({ type, limit: PAGE_SIZE, offset: page * PAGE_SIZE })
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
        setError(undefined);
      })
      .catch((e) => setError(String(e)));
  }, [type, page, refreshKey]);

  const download = async (incident: Incident) => {
    setBusy(incident.id);
    try {
      await api.downloadReport(incident.id);
      setItems((list) => list.map((i) => (i.id === incident.id ? { ...i, has_report: true } : i)));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(undefined);
    }
  };

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section className="panel">
      <div className="toolbar">
        <label>
          Violation{" "}
          <select value={type} onChange={(e) => { setType(e.target.value); setPage(0); }}>
            <option value="">All</option>
            {Object.entries(VIOLATION_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <span className="muted">{total} incidents</span>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Snapshot</th>
              <th>Time</th>
              <th>Camera</th>
              <th>Violation</th>
              <th>Severity</th>
              <th>Confidence</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id}>
                <td>
                  <a href={api.snapshotUrl(i.id)} target="_blank" rel="noreferrer">
                    <img className="thumb" src={api.snapshotUrl(i.id)} alt={`Snapshot of incident ${i.id}`} loading="lazy" />
                  </a>
                </td>
                <td>{new Date(i.created_at).toLocaleString()}</td>
                <td>
                  {i.camera_name}
                  <div className="muted">{i.zone}</div>
                </td>
                <td>{violationLabel(i.type)}</td>
                <td><SeverityBadge severity={i.severity} /></td>
                <td>{Math.round(i.confidence * 100)}%</td>
                <td>
                  <button className="btn" disabled={busy === i.id} onClick={() => download(i)}>
                    {busy === i.id ? "Writing report…" : i.has_report ? "Download report" : "Generate report"}
                  </button>
                </td>
              </tr>
            ))}
            {!items.length && (
              <tr><td colSpan={7} className="empty">No incidents yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="pager">
          <button className="btn btn-ghost" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</button>
          <span className="muted">Page {page + 1} of {pages}</span>
          <button className="btn btn-ghost" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>Next</button>
        </div>
      )}
    </section>
  );
}
