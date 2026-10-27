"""What happens when a camera worker raises an alert: snapshot, DB row, WebSocket push."""
import asyncio
import json
import logging
import uuid

import cv2
from fastapi import WebSocket

from .config import Settings
from .db.models import Incident
from .db.session import SessionLocal
from .vision.pipeline import Alert
from .vision.rules import SEVERITY

log = logging.getLogger(__name__)


class AlertHub:
    """Keeps the open dashboard WebSockets and broadcasts new incidents to them."""

    def __init__(self):
        self._clients: set[WebSocket] = set()
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket):
        self._clients.discard(ws)

    async def broadcast(self, message: dict):
        text = json.dumps(message)
        for ws in list(self._clients):
            try:
                await ws.send_text(text)
            except Exception:
                self.disconnect(ws)

    def broadcast_from_thread(self, message: dict):
        if self.loop is not None:
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)


class AlertRecorder:
    def __init__(self, settings: Settings, hub: AlertHub):
        self.snapshots_dir = settings.snapshots_dir
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.hub = hub

    def __call__(self, alert: Alert):
        """Runs on a camera worker thread."""
        snapshot = self.snapshots_dir / f"{uuid.uuid4().hex}.jpg"
        cv2.imwrite(str(snapshot), alert.frame)

        incident = Incident(
            camera_id=alert.camera.id,
            camera_name=alert.camera.name,
            zone=alert.camera.zone,
            type=alert.violation.type,
            severity=SEVERITY.get(alert.violation.type, "medium"),
            confidence=alert.violation.conf,
            box=list(alert.violation.box),
            snapshot_path=str(snapshot),
        )
        with SessionLocal() as session:
            session.add(incident)
            session.commit()

        log.info("Incident %s: %s on %s", incident.id, incident.type, incident.camera_id)
        self.hub.broadcast_from_thread({"event": "incident", "incident": incident.to_dict()})
