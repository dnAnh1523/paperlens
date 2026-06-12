from typing import Literal

from pydantic import BaseModel


class AnswerProviderStatusRead(BaseModel):
    provider_name: str
    provider_type: Literal["deterministic", "free-tier-api", "local-model", "unknown"]
    display_name: str
    is_default: bool
    is_available: bool
    requires_api_key: bool
    requires_network: bool
    requires_model_download: bool
    supports_streaming: bool
    status_message: str
