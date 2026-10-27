"""Turns raw detections into violations.

The PPE model only detects items that are present (Hard_hat, Vest, ...), never their
absence. So each Person box is checked for the required items: an item belongs to a
person when its center falls inside the body region where that item is worn.
"""
from .types import Detection, PersonStatus, RuleResult, Violation

PERSON_LABEL = "Person"

# Vertical band of the person box (0 = top, 1 = bottom) where the item's center must lie.
# Bands extend slightly past the box because helmets and boots often stick out of it.
PPE_REGIONS: dict[str, tuple[float, float]] = {
    "Hard_hat": (-0.15, 0.30),
    "Mask": (0.0, 0.30),
    "Vest": (0.15, 0.75),
    "Gloves": (0.25, 1.0),
    "Safety_boots": (0.70, 1.15),
}
HORIZONTAL_MARGIN = 0.10  # fraction of person width allowed outside the box sideways

VIOLATION_TYPES: dict[str, str] = {
    "Hard_hat": "NO_HARDHAT",
    "Mask": "NO_MASK",
    "Vest": "NO_VEST",
    "Gloves": "NO_GLOVES",
    "Safety_boots": "NO_BOOTS",
}

# Detector labels (lower-cased) that are violations on their own.
HAZARD_LABELS: dict[str, str] = {
    "fire": "FIRE",
    "smoke": "SMOKE",
    "fall": "FALL",
    "fallen": "FALL",
    "fall-detected": "FALL",
}

SEVERITY: dict[str, str] = {
    "FIRE": "critical",
    "FALL": "critical",
    "SMOKE": "high",
    "NO_HARDHAT": "high",
    "NO_VEST": "medium",
    "NO_MASK": "medium",
    "NO_GLOVES": "low",
    "NO_BOOTS": "low",
}


def item_belongs_to(item: Detection, person_box) -> bool:
    band = PPE_REGIONS.get(item.label)
    if band is None:
        return False
    px1, py1, px2, py2 = person_box
    width, height = px2 - px1, py2 - py1
    cx = (item.box[0] + item.box[2]) / 2
    cy = (item.box[1] + item.box[3]) / 2
    margin = HORIZONTAL_MARGIN * width
    top, bottom = band
    return (px1 - margin <= cx <= px2 + margin
            and py1 + top * height <= cy <= py1 + bottom * height)


def evaluate(detections: list[Detection], required_ppe: list[str]) -> RuleResult:
    persons: list[PersonStatus] = []
    hazards: list[Detection] = []
    violations: list[Violation] = []

    items = [d for d in detections if d.label in PPE_REGIONS]

    for det in detections:
        if det.label == PERSON_LABEL:
            status = PersonStatus(box=det.box, conf=det.conf)
            for required in required_ppe:
                if not any(i.label == required and item_belongs_to(i, det.box) for i in items):
                    status.missing.append(required)
                    violations.append(Violation(VIOLATION_TYPES[required], det.box, det.conf))
            persons.append(status)
        elif det.label.lower() in HAZARD_LABELS:
            hazards.append(det)
            violations.append(Violation(HAZARD_LABELS[det.label.lower()], det.box, det.conf))

    return RuleResult(persons=persons, hazards=hazards, violations=violations)
