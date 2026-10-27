import asyncio

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..config import get_settings

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("")
def list_cameras(request: Request):
    manager = request.app.state.cameras
    return [
        {
            "id": worker.camera.id,
            "name": worker.camera.name,
            "zone": worker.camera.zone,
            "online": worker.online,
            "detectors": [d.name for d in worker.detectors],
        }
        for worker in manager.workers.values()
    ]


@router.get("/{camera_id}/stream")
async def stream(camera_id: str, request: Request):
    """MJPEG stream of the annotated frames; usable directly as <img src>."""
    worker = request.app.state.cameras.workers.get(camera_id)
    if worker is None:
        raise HTTPException(404, "Unknown camera")
    delay = 1.0 / get_settings().stream_fps

    async def frames():
        while not await request.is_disconnected():
            jpeg = worker.latest_jpeg()
            if jpeg is not None:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            await asyncio.sleep(delay)

    return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")
