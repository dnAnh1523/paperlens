from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./data/sqlite/paperlens.db"
    local_storage_root: str = "./data/storage"
    qdrant_local_path: str = "./data/qdrant"
    qdrant_collection: str = "paperlens_chunks"
    openai_api_key: str = "replace_me"
    openai_model: str = "replace_me"
    openai_embedding_model: str = "replace_me"

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
