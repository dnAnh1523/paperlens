from typing import Literal

from pydantic import BaseModel


class AnswerProviderStatusRead(BaseModel):
    provider_name: str
    provider_type: Literal[
        "deterministic",
        "free-tier-api",
        "local-model",
        "openai-compatible",
        "unknown",
    ]
    display_name: str
    model_name: str | None
    base_url_host: str | None
    is_default: bool
    is_available: bool
    requires_api_key: bool
    requires_network: bool
    requires_model_download: bool
    supports_streaming: bool
    status_message: str
