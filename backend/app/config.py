from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    anthropic_api_key: str | None = None
    claude_model: str = "claude-opus-5-5"
    db_url: str = f"sqlite:///{(ROOT / 'storage' / 'smart_ehs.db').as_posix()}"
    storage_dir: Path = ROOT / "storage"
    osha_dir: Path = ROOT / "data" / "osha"
    cameras_file: Path = ROOT / "backend" / "app" / "cameras.yaml"
    device: str | None = None
    infer_fps: float = 5.0
    stream_fps: float = 10.0
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def snapshots_dir(self) -> Path:
        return self.storage_dir / "snapshots"

    @property
    def reports_dir(self) -> Path:
        return self.storage_dir / "reports"


class DetectorConfig(BaseModel):
    weights: Path
    conf: float = 0.4


class RulesConfig(BaseModel):
    required_ppe: list[str] = ["Hard_hat", "Vest"]
    debounce_frames: int = 5
    cooldown_seconds: float = 60.0


class CameraConfig(BaseModel):
    id: str
    name: str
    zone: str
    source: str
    detectors: list[str] = ["ppe"]
    enabled: bool = True


class SiteConfig(BaseModel):
    detectors: dict[str, DetectorConfig] = Field(default_factory=dict)
    rules: RulesConfig = Field(default_factory=RulesConfig)
    cameras: list[CameraConfig] = Field(default_factory=list)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_site_config(path: Path) -> SiteConfig:
    with open(path, encoding="utf-8") as f:
        config = SiteConfig.model_validate(yaml.safe_load(f) or {})
    # Relative paths in cameras.yaml are relative to the project root.
    for detector in config.detectors.values():
        if not detector.weights.is_absolute():
            detector.weights = ROOT / detector.weights
    for camera in config.cameras:
        if not camera.source.isdigit() and "://" not in camera.source and not Path(camera.source).is_absolute():
            camera.source = str(ROOT / camera.source)
    return config
