from __future__ import annotations

import os
import pytest
from sqlalchemy.orm import Session

# Set test environment defaults
os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"
os.environ["AI_PROVIDER"] = "mock"

from app.ai.base import AIProvider, AIProviderResult
from app.ai.exceptions import AIProviderError
from app.models.user import User
from app.services.ai_service import AIService


def _register_payload(email: str = "ai_tester@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "StrongPass123",
        "first_name": "AI",
        "last_name": "Tester",
    }


def _login(client, email: str = "ai_tester@example.com", password: str = "StrongPass123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def _setup_user(client, db_session: Session, email: str = "ai_tester@example.com"):
    client.post("/api/v1/auth/register", json=_register_payload(email))
    token = _login(client, email=email).json()["access_token"]
    user = db_session.query(User).filter(User.email == email).one()
    return token, user


def test_ai_unauthenticated(client):
    endpoints = [
        "/api/v1/ai/generate",
        "/api/v1/ai/rewrite",
        "/api/v1/ai/improve",
        "/api/v1/ai/shorten",
        "/api/v1/ai/expand",
        "/api/v1/ai/change-tone",
        "/api/v1/ai/adapt-platform",
        "/api/v1/ai/ideas",
    ]
    for endpoint in endpoints:
        res = client.post(endpoint, json={"content": "test", "prompt": "test", "topic": "test"})
        assert res.status_code == 401


def test_ai_generate_post(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_gen@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "prompt": "Launching our new summer collection featuring sustainable materials",
        "platform": "LINKEDIN",
        "tone": "PROFESSIONAL",
        "audience": "Eco-conscious fashion professionals",
        "objective": "Drive awareness and website traffic",
        "editorial_context": "Always inspiring, elegant, and eco-friendly.",
    }
    res = client.post("/api/v1/ai/generate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "GENERATE"
    assert "content" in data
    assert len(data["content"]) > 10
    assert data["usage"] is not None
    assert "api_key" not in str(data)
    assert "secret" not in str(data)


def test_ai_rewrite_content(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_rewrite@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "We made a new tool and it is fast and cool. Go check it out.",
        "tone": "CASUAL",
        "platform": "INSTAGRAM",
    }
    res = client.post("/api/v1/ai/rewrite", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "REWRITE"
    assert len(data["content"]) > 5


def test_ai_improve_content(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_improve@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "Our app helps schedule posts to facebook and linkedin.",
        "platform": "FACEBOOK",
    }
    res = client.post("/api/v1/ai/improve", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "IMPROVE"
    assert len(data["content"]) > 5


def test_ai_shorten_content(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_shorten@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "This is a very long text explaining everything in excessive detail that needs to be condensed into a single punchy tweet or post.",
        "platform": "LINKEDIN",
    }
    res = client.post("/api/v1/ai/shorten", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "SHORTEN"
    assert len(data["content"]) > 5


def test_ai_expand_content(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_expand@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "New product update out now.",
        "platform": "LINKEDIN",
    }
    res = client.post("/api/v1/ai/expand", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "EXPAND"
    assert len(data["content"]) > 10


def test_ai_change_tone(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_tone@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "Hey folks, check our latest update when you get a chance.",
        "tone": "FORMAL",
    }
    res = client.post("/api/v1/ai/change-tone", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "CHANGE_TONE"
    assert len(data["content"]) > 5


def test_ai_adapt_platform(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_adapt@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "content": "Our platform has reached 10,000 active users this month.",
        "platform": "INSTAGRAM",
    }
    res = client.post("/api/v1/ai/adapt-platform", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "ADAPT_PLATFORM"
    assert len(data["content"]) > 5


def test_ai_generate_ideas(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_ideas@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "topic": "SaaS Community Growth and Customer Retention Strategies",
        "platform": "LINKEDIN",
        "tone": "PROFESSIONAL",
        "target_audience": "Tech Startup Founders and Community Managers",
    }
    res = client.post("/api/v1/ai/ideas", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["action"] == "IDEATE"
    assert data["ideas"] is not None
    assert len(data["ideas"]) >= 3


def test_ai_validation_error(client, db_session: Session):
    token, _ = _setup_user(client, db_session, "ai_val@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Empty prompt
    res = client.post("/api/v1/ai/generate", json={"prompt": ""}, headers=headers)
    assert res.status_code == 422

    # Invalid platform enum
    res2 = client.post(
        "/api/v1/ai/generate",
        json={"prompt": "Valid prompt", "platform": "TIKTOK_INVALID"},
        headers=headers,
    )
    assert res2.status_code == 422


class FaultyAIProvider(AIProvider):
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIProviderResult:
        raise AIProviderError("Provider upstream timeout or quota error", status_code=504)


def test_ai_provider_error_handling(monkeypatch):
    service = AIService(provider=FaultyAIProvider())
    from app.schemas.ai import AIGenerateRequest, AITone
    req = AIGenerateRequest(prompt="Test prompt", tone=AITone.PROFESSIONAL)
    with pytest.raises(AIProviderError) as exc_info:
        service.generate_post(req)
    assert exc_info.value.status_code == 504
    assert "upstream timeout" in exc_info.value.message
