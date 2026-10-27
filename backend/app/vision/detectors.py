import logging
import threading

import numpy as np

from ..config import DetectorConfig
from .types import Detection

log = logging.getLogger(__name__)


class YoloDetector:
    """One YOLO model, shared by every camera that uses it (inference is serialized by a lock)."""

    def __init__(self, name: str, config: DetectorConfig, device: str | None = None):
        from ultralytics import YOLO  # heavy import, only when a model is actually loaded

        self.name = name
        self.conf = config.conf
        self.device = device
        self.model = YOLO(str(config.weights))
        self._lock = threading.Lock()

    def predict(self, frame: np.ndarray) -> list[Detection]:
        with self._lock:
            result = self.model.predict(frame, conf=self.conf, device=self.device, verbose=False)[0]
        names = result.names
        return [
            Detection(label=names[int(cls)], conf=float(conf), box=tuple(map(float, xyxy)), model=self.name)
            for xyxy, conf, cls in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist(),
                                       result.boxes.cls.tolist())
        ]


def build_detectors(configs: dict[str, DetectorConfig], device: str | None) -> dict[str, YoloDetector]:
    detectors = {}
    for name, config in configs.items():
        if not config.weights.is_file():
            log.warning("Detector %r skipped: weights not found at %s", name, config.weights)
            continue
        detectors[name] = YoloDetector(name, config, device)
        log.info("Loaded detector %r (%s)", name, config.weights.name)
    return detectors
