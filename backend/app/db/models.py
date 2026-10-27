from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    camera_id: Mapped[str] = mapped_column(String(64), index=True)
    camera_name: Mapped[str] = mapped_column(String(128))
    zone: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float)
    box: Mapped[list[float]] = mapped_column(JSON)
    snapshot_path: Mapped[str] = mapped_column(String(512))
    report_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    @property
    def created_at_utc(self) -> datetime:
        # SQLite drops the timezone on read; stored values are always UTC.
        return self.created_at if self.created_at.tzinfo else self.created_at.replace(tzinfo=timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at_utc.isoformat(),
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "zone": self.zone,
            "type": self.type,
            "severity": self.severity,
            "confidence": round(self.confidence, 3),
            "has_report": self.report_path is not None,
        }
