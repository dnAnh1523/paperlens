import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.generation.answer_service import get_answer_provider_status
from app.main import app


def test_deterministic_answer_provider_status() -> None:
    status = get_answer_provider_status("deterministic-evidence")

    assert status.provider_name == "deterministic-evidence"
    assert status.provider_type == "deterministic"
    assert status.display_name == "Deterministic evidence preview"
    assert status.is_default is True
    assert status.is_available is True
    assert status.requires_api_key is False
    assert status.requires_network is False
    assert status.requires_model_download is False
    assert status.supports_streaming is False
    assert "does not call an LLM" in status.status_message


def test_answer_provider_status_endpoint_reports_default_provider() -> None:
    client = TestClient(app)

    response = client.get("/answer-provider/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "provider_name": "deterministic-evidence",
        "provider_type": "deterministic",
        "display_name": "Deterministic evidence preview",
        "is_default": True,
        "is_available": True,
        "requires_api_key": False,
        "requires_network": False,
        "requires_model_download": False,
        "supports_streaming": False,
        "status_message": (
            "Default local deterministic provider is available. It creates evidence-preview "
            "answers from retrieved chunks and does not call an LLM."
        ),
    }


def test_answer_provider_status_endpoint_reports_unsupported_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "answer_provider", "future-free-tier-provider")
    client = TestClient(app)

    response = client.get("/answer-provider/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_name"] == "future-free-tier-provider"
    assert payload["provider_type"] == "unknown"
    assert payload["display_name"] == "future-free-tier-provider"
    assert payload["is_default"] is False
    assert payload["is_available"] is False
    assert payload["requires_api_key"] is False
    assert payload["requires_network"] is False
    assert payload["requires_model_download"] is False
    assert payload["supports_streaming"] is False
    assert "Unsupported answer provider" in payload["status_message"]
