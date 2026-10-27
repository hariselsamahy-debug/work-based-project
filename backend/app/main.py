import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .alerts import AlertHub, AlertRecorder
from .api import cameras, incidents, reports, ws
from .config import get_settings, load_site_config
from .db.session import init_db
from .reports.service import ReportService
from .vision.pipeline import CameraManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()

    hub = AlertHub()
    hub.loop = asyncio.get_running_loop()
    site = load_site_config(settings.cameras_file)
    manager = CameraManager(site, settings.device, settings.infer_fps, AlertRecorder(settings, hub))

    app.state.hub = hub
    app.state.cameras = manager
    app.state.reports = ReportService(settings)

    manager.start()
    yield
    manager.stop()


app = FastAPI(title="Smart-EHS", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins,
                   allow_methods=["*"], allow_headers=["*"])

for module in (cameras, incidents, reports, ws):
    app.include_router(module.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
