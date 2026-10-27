"""Per-camera loop: frame -> detectors -> rules -> annotated frame + alerts."""
import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable

import cv2
import numpy as np

from ..config import CameraConfig, SiteConfig
from .annotate import annotate
from .camera import CameraStream
from .detectors import YoloDetector, build_detectors
from .rules import evaluate
from .tracker import EventTracker
from .types import Violation

log = logging.getLogger(__name__)


@dataclass
class Alert:
    camera: CameraConfig
    violation: Violation
    frame: np.ndarray  # annotated frame at the moment of the alert


AlertHandler = Callable[[Alert], None]


class CameraWorker:
    def __init__(self, camera: CameraConfig, detectors: list[YoloDetector], required_ppe: list[str],
                 tracker: EventTracker, on_alert: AlertHandler, infer_fps: float):
        self.camera = camera
        self.stream = CameraStream(camera.id, camera.source)
        self.detectors = detectors
        self.required_ppe = required_ppe
        self.tracker = tracker
        self.on_alert = on_alert
        self.interval = 1.0 / infer_fps
        self._jpeg: bytes | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"worker-{camera.id}", daemon=True)

    @property
    def online(self) -> bool:
        return self.stream.online

    def latest_jpeg(self) -> bytes | None:
        return self._jpeg

    def start(self):
        self.stream.start()
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=5)
        self.stream.stop()

    def _run(self):
        while not self._stop.is_set():
            started = time.monotonic()
            frame = self.stream.latest()
            if frame is not None:
                try:
                    self._process(frame)
                except Exception:
                    log.exception("Camera %s: processing failed", self.camera.id)
            self._stop.wait(max(0.0, self.interval - (time.monotonic() - started)))

    def _process(self, frame: np.ndarray):
        detections = [d for detector in self.detectors for d in detector.predict(frame)]
        result = evaluate(detections, self.required_ppe)
        annotated = annotate(frame, detections, result)
        ok, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            self._jpeg = jpeg.tobytes()

        fired = self.tracker.update(self.camera.id, {v.type for v in result.violations})
        for vtype in fired:
            violation = max((v for v in result.violations if v.type == vtype), key=lambda v: v.conf)
            self.on_alert(Alert(self.camera, violation, annotated))


class CameraManager:
    def __init__(self, site: SiteConfig, device: str | None, infer_fps: float, on_alert: AlertHandler):
        detectors = build_detectors(site.detectors, device)
        tracker = EventTracker(site.rules.debounce_frames, site.rules.cooldown_seconds)
        self.workers: dict[str, CameraWorker] = {}
        for camera in site.cameras:
            if not camera.enabled:
                continue
            missing = [name for name in camera.detectors if name not in detectors]
            if missing:
                log.warning("Camera %s: detectors %s not loaded", camera.id, missing)
            self.workers[camera.id] = CameraWorker(
                camera,
                [detectors[name] for name in camera.detectors if name in detectors],
                site.rules.required_ppe,
                tracker,
                on_alert,
                infer_fps,
            )

    def start(self):
        for worker in self.workers.values():
            worker.start()

    def stop(self):
        for worker in self.workers.values():
            worker.stop()
