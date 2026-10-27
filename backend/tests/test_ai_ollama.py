from __future__ import annotations

import httpx
import pytest
from unittest.mock import MagicMock, patch

from app.ai.base import AIProviderResult
from app.ai.exceptions import AIProviderError
from app.ai.providers.mock import MockAIProvider
from app.ai.providers.ollama import OllamaProvider
from app.models.user import User
from app.schemas.ai import (
    AIAction,
    AIGenerateRequest,
    AIRewriteRequest,
    AIImproveRequest,
    AIShortenRequest,
    AIExpandRequest,
    AIChangeToneRequest,
    AIAdaptPlatformRequest,
    AIIdeasRequest,
    AIPlatform,
    AITone,
)
from app.services.ai_service import AIService


def _register_payload(email: str = "ollama_test@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "StrongPassword123!",
        "first_name": "Ollama",
        "last_name": "Tester",
    }


def _setup_user(client, db_session, email: str = "ollama_test@example.com"):
    client.post("/api/v1/auth/register", json=_register_payload(email))
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = login_res.json()["access_token"]
    user = db_session.query(User).filter(User.email == email).one()
    return token, user


# ==============================================================================
# Unit Tests: OllamaProvider direct tests (mocking httpx)
# ==============================================================================

def test_ollama_provider_init_defaults():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
    assert provider.base_url == "http://localhost:11434"
    assert provider.model == "llama3.2:3b"
    assert provider.timeout == 60.0


def test_ollama_provider_check_availability_success():
    provider = OllamaProvider(base_url="http://ollama-test:11434", model="llama3.2:3b")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "llama3.2:3b"},
            {"name": "mistral:latest"},
        ]
    }

    with patch("httpx.Client.get", return_value=mock_response):
        status = provider.check_availability()
        assert status["available"] is True
        assert status["provider"] == "ollama"
        assert status["model"] == "llama3.2:3b"
        assert "llama3.2:3b" in status["installed_models"]


def test_ollama_provider_check_availability_model_missing():
    provider = OllamaProvider(base_url="http://ollama-test:11434", model="llama3.2:3b")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "codellama:7b"},
        ]
    }

    with patch("httpx.Client.get", return_value=mock_response):
        status = provider.check_availability()
        assert status["available"] is False
        assert "not installed" in status["error"]
        assert status["installed_models"] == ["codellama:7b"]


def test_ollama_provider_check_availability_connection_error():
    provider = OllamaProvider(base_url="http://ollama-test:11434", model="llama3.2:3b")

    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Connection refused")):
        status = provider.check_availability()
        assert status["available"] is False
        assert "unreachable" in status["error"]
        assert status["installed_models"] == []


def test_ollama_provider_generate_success():
    provider = OllamaProvider(base_url="http://ollama-test:11434", model="llama3.2:3b")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "llama3.2:3b",
        "message": {
            "role": "assistant",
            "content": "✨ Découvrez notre nouvelle offre exclusive ! 🚀 #Innovation",
        },
        "prompt_eval_count": 45,
        "eval_count": 85,
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        result = provider.generate(
            prompt="Présentation nouveau produit",
            system_prompt="Tu es un community manager expert.",
            temperature=0.7,
            max_tokens=500,
        )

        assert mock_post.called
        call_url = mock_post.call_args[0][0]
        call_payload = mock_post.call_args[1]["json"]

        assert call_url == "http://ollama-test:11434/api/chat"
        assert call_payload["model"] == "llama3.2:3b"
        assert len(call_payload["messages"]) == 2
        assert call_payload["messages"][0]["role"] == "system"
        assert call_payload["messages"][1]["role"] == "user"
        assert call_payload["options"]["temperature"] == 0.7
        assert call_payload["options"]["num_predict"] == 500

        assert "Découvrez notre nouvelle offre" in result.content
        assert result.prompt_tokens == 45
        assert result.completion_tokens == 85
        assert result.total_tokens == 130


def test_ollama_provider_generate_model_404():
    provider = OllamaProvider(base_url="http://ollama-test:11434", model="llama3.2:3b")

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "model not found"

    with patch("httpx.Client.post", return_value=mock_response):
        with pytest.raises(AIProviderError) as exc_info:
            provider.generate(prompt="Test prompt")
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.message


def test_ollama_provider_generate_server_unreachable_503():
    provider = OllamaProvider(base_url="http://ollama-test:11434", model="llama3.2:3b")

    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Failed to connect")):
        with pytest.raises(AIProviderError) as exc_info:
            provider.generate(prompt="Test prompt")
        assert exc_info.value.status_code == 503
        assert "unreachable" in exc_info.value.message


def test_ollama_provider_generate_timeout_504():
    provider = OllamaProvider(base_url="http://ollama-test:11434", model="llama3.2:3b")

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timeout")):
        with pytest.raises(AIProviderError) as exc_info:
            provider.generate(prompt="Test prompt")
        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.message


# ==============================================================================
# Unit Tests: AIService Integration with OllamaProvider
# ==============================================================================

def test_ai_service_generate_post_prompt_composition():
    mock_provider = MagicMock(spec=OllamaProvider)
    mock_provider.generate.return_value = AIProviderResult(
        content="Voici le post généré pour LinkedIn.",
        prompt_tokens=30,
        completion_tokens=60,
        total_tokens=90,
    )

    service = AIService(provider=mock_provider)
    payload = AIGenerateRequest(
        prompt="Lancement de notre nouveau service éco-responsable",
        platform=AIPlatform.LINKEDIN,
        tone=AITone.HUMOROUS,
        audience="Responsables RSE et startups",
        objective="Générer de l'engagement et des partages",
        editorial_context="Mettre en avant l'authenticité et l'impact positif.",
        language="fr",
        length="short",
        include_hashtags=True,
        include_cta=True,
    )

    result = service.generate_post(payload)

    assert result.action == AIAction.GENERATE
    assert result.content == "Voici le post généré pour LinkedIn."
    assert result.usage.total_tokens == 90

    # Verify that the generated prompt sent to provider includes all expected constraints
    mock_provider.generate.assert_called_once()
    call_kwargs = mock_provider.generate.call_args[1]
    user_prompt = call_kwargs["prompt"]
    system_prompt = call_kwargs["system_prompt"]

    assert "Lancement de notre nouveau service" in user_prompt
    assert "Responsables RSE" in user_prompt
    assert "Générer de l'engagement" in user_prompt

    full_context = f"{system_prompt}\n{user_prompt}".lower()
    assert "french" in full_context or "français" in full_context
    assert "short" in full_context or "court" in full_context
    assert "hashtag" in full_context
    assert "call to action" in full_context or "cta" in full_context
    assert "linkedin" in full_context
    assert "humorous" in full_context or "humoristique" in full_context
    assert "impact positif" in full_context


def test_ai_service_rewrite_content_with_ollama():
    mock_provider = MagicMock(spec=OllamaProvider)
    mock_provider.generate.return_value = AIProviderResult(
        content="Texte réécrit avec succès.",
        prompt_tokens=25,
        completion_tokens=50,
        total_tokens=75,
    )

    service = AIService(provider=mock_provider)
    payload = AIRewriteRequest(
        content="Notre application est super rapide et tout le monde l'aime.",
        platform=AIPlatform.INSTAGRAM,
        tone=AITone.FRIENDLY,
        language="fr",
        include_hashtags=True,
        include_cta=True,
    )

    result = service.rewrite_content(payload)
    assert result.action == AIAction.REWRITE
    assert result.content == "Texte réécrit avec succès."

    call_kwargs = mock_provider.generate.call_args[1]
    assert "Notre application est super rapide" in call_kwargs["prompt"]
    full_context = f"{call_kwargs['system_prompt']}\n{call_kwargs['prompt']}".lower()
    assert "instagram" in full_context
    assert "friendly" in full_context


def test_ai_service_ideate_parses_list_of_ideas():
    mock_provider = MagicMock(spec=OllamaProvider)
    mock_provider.generate.return_value = AIProviderResult(
        content=(
            "1. Les 5 piliers d'une communication éco-responsable réussie\n"
            "2. Témoignage client : comment réduire son empreinte carbone en entreprise\n"
            "3. Les coulisses de la création de nos produits zéro déchet\n"
            "4. Débat : le télétravail est-il vraiment plus écologique ?\n"
            "5. Infographie interactive sur le recyclage en milieu professionnel"
        ),
        prompt_tokens=20,
        completion_tokens=80,
        total_tokens=100,
    )

    service = AIService(provider=mock_provider)
    payload = AIIdeasRequest(
        topic="Écologie et développement durable en entreprise",
        platform=AIPlatform.LINKEDIN,
        language="fr",
    )

    result = service.generate_ideas(payload)
    assert result.action == AIAction.IDEATE
    assert result.ideas is not None
    assert len(result.ideas) >= 5
    assert "Les 5 piliers d'une communication" in result.ideas[0]


def test_ai_service_status_endpoint(client, db_session):
    token, _ = _setup_user(client, db_session, "ollama_status@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/ai/status", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "provider" in data
    assert "model" in data
    assert "available" in data
    assert isinstance(data["available"], bool)
    assert "installed_models" in data
