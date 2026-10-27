import type { Severity } from "../api";

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <span className={`badge badge-${severity}`}>{severity}</span>;
}
