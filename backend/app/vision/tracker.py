"""Decides when a per-frame violation becomes an alert.

Single-frame detections flicker, and an unhelmeted worker should raise one alert,
not one every frame. A violation type must be present for `debounce_frames`
consecutive frames on a camera to fire, then that camera + type stays quiet for
`cooldown_seconds`.
"""
import threading
import time
from collections import defaultdict
from typing import Callable


class EventTracker:
    def __init__(self, debounce_frames: int, cooldown_seconds: float,
                 clock: Callable[[], float] = time.monotonic):
        self.debounce_frames = debounce_frames
        self.cooldown_seconds = cooldown_seconds
        self.clock = clock
        self._streak: dict[tuple[str, str], int] = defaultdict(int)
        self._last_fired: dict[tuple[str, str], float] = {}
        self._lock = threading.Lock()  # shared by all camera workers

    def update(self, camera_id: str, present_types: set[str]) -> list[str]:
        """Feed the violation types seen in one frame; returns the types that should alert now."""
        with self._lock:
            return self._update(camera_id, present_types)

    def _update(self, camera_id: str, present_types: set[str]) -> list[str]:
        now = self.clock()
        fired = []

        for key in [k for k in self._streak if k[0] == camera_id and k[1] not in present_types]:
            del self._streak[key]

        for vtype in sorted(present_types):
            key = (camera_id, vtype)
            self._streak[key] += 1
            if self._streak[key] < self.debounce_frames:
                continue
            last = self._last_fired.get(key)
            if last is None or now - last >= self.cooldown_seconds:
                self._last_fired[key] = now
                fired.append(vtype)
        return fired
