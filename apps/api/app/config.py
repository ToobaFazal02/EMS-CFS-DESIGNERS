from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CFS Designers"
    secret_key: str = "dev-secret-change-me"
    ems_env: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./ems_data/ems.db"
    access_token_expire_minutes: int = 720
    data_dir: str = "./ems_data"
    screenshot_retention_days: int = 60
    idle_seconds: int = 180
    overtime_hours_per_day: float = 8.0
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    timezone: str = "Asia/Karachi"
    auto_seed_samples: bool = False

    def secret_is_weak(self) -> bool:
        key = (self.secret_key or "").strip()
        if len(key) < 32:
            return True
        lowered = key.lower()
        if lowered.startswith("change-me") or "change-me" in lowered:
            return True
        if lowered in {"dev-secret-change-me", "secret", "changeme"}:
            return True
        return False

    @property
    def is_production(self) -> bool:
        return self.ems_env.strip().lower() in {"prod", "production"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        (p / "screenshots").mkdir(exist_ok=True)
        (p / "reports").mkdir(exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
