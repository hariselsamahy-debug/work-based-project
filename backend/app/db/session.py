from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import get_settings
from .models import Base

_settings = get_settings()
_settings.storage_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    _settings.db_url,
    # Camera worker threads write incidents, so SQLite must allow cross-thread use.
    connect_args={"check_same_thread": False} if _settings.db_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def init_db():
    Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
