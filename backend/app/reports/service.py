from pathlib import Path

import anthropic

from ..config import Settings
from ..db.models import Incident
from .llm import write_report
from .osha_index import OshaIndex
from .pdf import render_pdf
from .violation_map import describe


class ReportService:
    def __init__(self, settings: Settings):
        self.model = settings.claude_model
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self.index = OshaIndex.from_dir(settings.osha_dir)
        self.reports_dir = settings.reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def build(self, incident: Incident) -> Path:
        violation = describe(incident.type)
        data = {
            "id": incident.id,
            "time": incident.created_at_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "camera_id": incident.camera_id,
            "camera_name": incident.camera_name,
            "zone": incident.zone,
            "type": incident.type,
            "severity": incident.severity,
            "confidence": incident.confidence,
        }
        snapshot = Path(incident.snapshot_path)
        chunks = self.index.search(violation["query"])
        report = write_report(self.client, self.model, data, violation, chunks, snapshot.read_bytes())

        path = self.reports_dir / f"incident-{incident.id}.pdf"
        render_pdf(path, data, violation["title"], report, snapshot)
        return path
