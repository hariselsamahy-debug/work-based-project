from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Incident
from ..db.session import get_db

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


def get_incident(incident_id: int, db: Session = Depends(get_db)) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(404, "Incident not found")
    return incident


@router.get("")
def list_incidents(camera_id: str | None = None, type: str | None = None,
                   limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    query = select(Incident)
    if camera_id:
        query = query.where(Incident.camera_id == camera_id)
    if type:
        query = query.where(Incident.type == type)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Incident.created_at.desc()).limit(min(limit, 200)).offset(offset))
    return {"total": total, "items": [row.to_dict() for row in rows]}


@router.get("/{incident_id}")
def read_incident(incident: Incident = Depends(get_incident)):
    return incident.to_dict()


@router.get("/{incident_id}/snapshot")
def snapshot(incident: Incident = Depends(get_incident)):
    return FileResponse(incident.snapshot_path, media_type="image/jpeg")
