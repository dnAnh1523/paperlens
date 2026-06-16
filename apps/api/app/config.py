from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./data/sqlite/paperlens.db"
    local_storage_root: str = "./data/storage"
    answer_provider: str = "deterministic-evidence"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = 30.0
    llm_max_tokens: int = 700
    llm_temperature: float = 0.0
    llm_requires_api_key: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def storage_path(self) -> Path:
        return Path(self.local_storage_root)

    @property
    def sqlite_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        return Path("./data/sqlite/paperlens.db")


settings = Settings()
