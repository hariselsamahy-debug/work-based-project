export type Severity = "critical" | "high" | "medium" | "low";

export interface Camera {
  id: string;
  name: string;
  zone: string;
  online: boolean;
  detectors: string[];
}

export interface Incident {
  id: number;
  created_at: string;
  camera_id: string;
  camera_name: string;
  zone: string;
  type: string;
  severity: Severity;
  confidence: number;
  has_report: boolean;
}

export const VIOLATION_LABELS: Record<string, string> = {
  NO_HARDHAT: "No hard hat",
  NO_VEST: "No safety vest",
  NO_MASK: "No mask",
  NO_GLOVES: "No gloves",
  NO_BOOTS: "No safety boots",
  FIRE: "Fire",
  SMOKE: "Smoke",
  FALL: "Worker fall",
};

export const violationLabel = (type: string) => VIOLATION_LABELS[type] ?? type;

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const api = {
  cameras: () => fetch("/api/cameras").then(json<Camera[]>),

  incidents: (params: { camera_id?: string; type?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && query.set(k, String(v)));
    return fetch(`/api/incidents?${query}`).then(json<{ total: number; items: Incident[] }>);
  },

  streamUrl: (cameraId: string) => `/api/cameras/${encodeURIComponent(cameraId)}/stream`,
  snapshotUrl: (incidentId: number) => `/api/incidents/${incidentId}/snapshot`,

  /** Generates (first time) and downloads the PDF report. */
  async downloadReport(incidentId: number) {
    const res = await fetch(`/api/incidents/${incidentId}/report`, { method: "POST" });
    if (!res.ok) throw new Error(`Report failed: ${res.status}`);
    const url = URL.createObjectURL(await res.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = `incident-${incidentId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  },
};
