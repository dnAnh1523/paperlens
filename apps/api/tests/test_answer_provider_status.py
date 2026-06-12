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
    assert status.model_name == "evidence-preview-template-v1"
    assert status.base_url_host is None
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
        "model_name": "evidence-preview-template-v1",
        "base_url_host": None,
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
    assert payload["model_name"] is None
    assert payload["base_url_host"] is None
    assert payload["is_default"] is False
    assert payload["is_available"] is False
    assert payload["requires_api_key"] is False
    assert payload["requires_network"] is False
    assert payload["requires_model_download"] is False
    assert payload["supports_streaming"] is False
    assert "Unsupported answer provider" in payload["status_message"]


def test_answer_provider_status_reports_openai_compatible_missing_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "answer_provider", "openai-compatible")
    monkeypatch.setattr(settings, "llm_base_url", None)
    monkeypatch.setattr(settings, "llm_model", None)
    monkeypatch.setattr(settings, "llm_api_key", None)
    monkeypatch.setattr(settings, "llm_requires_api_key", False)
    client = TestClient(app)

    response = client.get("/answer-provider/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_name"] == "openai-compatible"
    assert payload["provider_type"] == "openai-compatible"
    assert payload["display_name"] == "OpenAI-compatible chat completions"
    assert payload["model_name"] is None
    assert payload["base_url_host"] is None
    assert payload["is_default"] is False
    assert payload["is_available"] is False
    assert payload["requires_api_key"] is False
    assert payload["requires_network"] is True
    assert payload["requires_model_download"] is False
    assert payload["supports_streaming"] is False
    assert "llm_base_url is required" in payload["status_message"]


def test_answer_provider_status_reports_openai_compatible_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "answer_provider", "openai-compatible")
    monkeypatch.setattr(settings, "llm_base_url", "https://api.example.test/v1")
    monkeypatch.setattr(settings, "llm_model", "free-model")
    monkeypatch.setattr(settings, "llm_api_key", "secret-value")
    monkeypatch.setattr(settings, "llm_requires_api_key", True)
    client = TestClient(app)

    response = client.get("/answer-provider/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_name"] == "openai-compatible"
    assert payload["provider_type"] == "openai-compatible"
    assert payload["display_name"] == "OpenAI-compatible chat completions"
    assert payload["model_name"] == "free-model"
    assert payload["base_url_host"] == "api.example.test"
    assert payload["is_available"] is True
    assert payload["requires_api_key"] is True
    assert payload["requires_network"] is True
    assert payload["requires_model_download"] is False
    assert payload["supports_streaming"] is False
    assert "secret-value" not in str(payload)
