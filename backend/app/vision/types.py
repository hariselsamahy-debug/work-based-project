from dataclasses import dataclass, field

Box = tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels


@dataclass(frozen=True)
class Detection:
    label: str
    conf: float
    box: Box
    model: str = ""


@dataclass
class PersonStatus:
    box: Box
    conf: float
    missing: list[str] = field(default_factory=list)

    @property
    def compliant(self) -> bool:
        return not self.missing


@dataclass(frozen=True)
class Violation:
    type: str  # e.g. NO_HARDHAT, FIRE, FALL
    box: Box
    conf: float


@dataclass
class RuleResult:
    persons: list[PersonStatus]
    hazards: list[Detection]
    violations: list[Violation]
