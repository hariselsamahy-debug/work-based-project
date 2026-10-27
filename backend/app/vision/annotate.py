import cv2
import numpy as np

from .types import Detection, RuleResult

RED = (0, 0, 255)
GREEN = (0, 200, 0)
GREY = (180, 180, 180)


def _label(frame, text, x, y, color):
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    y = max(y, h + 6)
    cv2.rectangle(frame, (x, y - h - 6), (x + w + 6, y), color, -1)
    cv2.putText(frame, text, (x + 3, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def _rect(frame, box, color, thickness):
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    return x1, y1


def annotate(frame: np.ndarray, detections: list[Detection], result: RuleResult) -> np.ndarray:
    """Red box = person missing PPE or hazard, green = compliant person, grey = PPE items."""
    out = frame.copy()
    for det in detections:
        if det.label != "Person" and det not in result.hazards:
            _rect(out, det.box, GREY, 1)
    for person in result.persons:
        color = GREEN if person.compliant else RED
        x, y = _rect(out, person.box, color, 2)
        text = "OK" if person.compliant else "Missing: " + ", ".join(person.missing)
        _label(out, text, x, y, color)
    for hazard in result.hazards:
        x, y = _rect(out, hazard.box, RED, 3)
        _label(out, f"{hazard.label.upper()} {hazard.conf:.0%}", x, y, RED)
    return out
