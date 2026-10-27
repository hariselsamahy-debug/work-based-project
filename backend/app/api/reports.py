from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db.models import Incident
from ..db.session import get_db
from .incidents import get_incident

router = APIRouter(prefix="/api/incidents", tags=["reports"])


@router.post("/{incident_id}/report")
async def create_report(request: Request, incident: Incident = Depends(get_incident),
                        db: Session = Depends(get_db)):
    """Generates the PDF on first request (LLM call), then serves the cached file."""
    if incident.report_path is None or not Path(incident.report_path).is_file():
        path = await run_in_threadpool(request.app.state.reports.build, incident)
        incident.report_path = str(path)
        db.commit()
    return FileResponse(incident.report_path, media_type="application/pdf",
                        filename=f"incident-{incident.id}.pdf")
