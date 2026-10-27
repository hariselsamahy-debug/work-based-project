import logging
import threading
import time

import cv2
import numpy as np

log = logging.getLogger(__name__)

RECONNECT_DELAY = 2.0


class CameraStream:
    """Reads a camera in its own thread and keeps only the newest frame.

    Video files loop at their native frame rate so they behave like a live camera.
    """

    def __init__(self, camera_id: str, source: str):
        self.camera_id = camera_id
        self.source = int(source) if source.isdigit() else source
        self.is_file = isinstance(self.source, str) and "://" not in self.source
        self._frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"camera-{camera_id}", daemon=True)
        self.online = False

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=5)

    def latest(self) -> np.ndarray | None:
        with self._lock:
            return self._frame

    def _run(self):
        while not self._stop.is_set():
            cap = cv2.VideoCapture(self.source)
            if not cap.isOpened():
                self.online = False
                log.warning("Camera %s: cannot open %s, retrying", self.camera_id, self.source)
                self._stop.wait(RECONNECT_DELAY)
                continue

            self.online = True
            frame_delay = 1.0 / (cap.get(cv2.CAP_PROP_FPS) or 25.0) if self.is_file else 0.0
            while not self._stop.is_set():
                started = time.monotonic()
                ok, frame = cap.read()
                if not ok:
                    if self.is_file:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    log.warning("Camera %s: stream lost, reconnecting", self.camera_id)
                    break
                with self._lock:
                    self._frame = frame
                if frame_delay:
                    self._stop.wait(max(0.0, frame_delay - (time.monotonic() - started)))
            cap.release()
            self.online = False
