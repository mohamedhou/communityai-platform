from __future__ import annotations

import os

# Set test environment defaults before imports
os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from sqlalchemy.orm import Session

from app.core.encryption import encrypt_token, decrypt_token
from app.core.config import get_settings
from app.models.user import User
from app.social.models import OAuthState, SocialAccount, SocialAccountStatus


def _register_payload(email: str = "alice@example.com") -> dict[str, str]:
    return {
        "email": email,
        "password": "StrongPass123",
        "first_name": "Alice",
        "last_name": "Martin",
    }


def _login(client, email: str = "alice@example.com", password: str = "StrongPass123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_list_accounts_unauthenticated(client):
    res = client.get("/api/v1/social-accounts")
    assert res.status_code == 401


def test_list_accounts_authenticated_empty(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    token = _login(client).json()["access_token"]

    res = client.get("/api/v1/social-accounts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json() == []


def test_connect_url_generation(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload())
    token = _login(client).json()["access_token"]

    res = client.get(
        "/api/v1/social-accounts/meta/connect",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "url" in body
    assert "state=" in body["url"]

    # Verify state is saved in the database
    state_in_db = db_session.query(OAuthState).first()
    assert state_in_db is not None
    assert state_in_db.state in body["url"]


def test_callback_valid_state_connects_meta(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload())
    token = _login(client).json()["access_token"]

    # 1. Get connect URL to generate state
    connect_res = client.get(
        "/api/v1/social-accounts/meta/connect",
        headers={"Authorization": f"Bearer {token}"},
    )
    state = db_session.query(OAuthState).first().state

    # 2. Trigger callback with valid state
    # GET callback does not require auth headers because state authenticates the user context
    callback_res = client.get(
        f"/api/v1/social-accounts/meta/callback?code=mock-code&state={state}",
        follow_redirects=False,
    )
    assert callback_res.status_code == 307  # Temporary Redirect
    assert callback_res.headers["location"] == "http://localhost:5173/social-accounts"

    # 3. Check that accounts are created in DB
    accounts = db_session.query(SocialAccount).all()
    assert len(accounts) == 2  # Meta returns mock Facebook and Instagram Page
    
    fb = next(a for a in accounts if a.platform == "facebook")
    assert fb.account_name == "Mock Facebook Page"
    assert fb.status == SocialAccountStatus.CONNECTED
    # Verify token is encrypted in DB
    assert fb.access_token_encrypted != "mock-meta-access-token"
    assert decrypt_token(fb.access_token_encrypted) == "mock-meta-access-token"

    ig = next(a for a in accounts if a.platform == "instagram")
    assert ig.account_name == "Mock Instagram Professional"
    
    # 4. Check list accounts returns safe representations (no tokens)
    list_res = client.get(
        "/api/v1/social-accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    list_body = list_res.json()
    assert len(list_body) == 2
    for item in list_body:
        assert "access_token" not in item
        assert "refresh_token" not in item
        assert "access_token_encrypted" not in item


def test_callback_invalid_state(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    
    callback_res = client.get(
        "/api/v1/social-accounts/meta/callback?code=mock-code&state=invalid-state-uuid",
        follow_redirects=False,
    )
    assert callback_res.status_code == 307
    assert "error=state_invalid_or_expired" in callback_res.headers["location"]


def test_disconnect_and_rbac(client, db_session: Session):
    # Setup User A
    client.post("/api/v1/auth/register", json=_register_payload("user_a@example.com"))
    token_a = _login(client, email="user_a@example.com") .json()["access_token"]
    user_a = db_session.query(User).filter(User.email == "user_a@example.com").one()

    # Create manual social account for User A
    account = SocialAccount(
        user_id=user_a.id,
        platform="linkedin",
        provider="linkedin",
        external_account_id="linkedin-a-123",
        account_name="Alice LinkedIn",
        access_token_encrypted=encrypt_token("access-a"),
        status=SocialAccountStatus.CONNECTED,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # Setup User B
    client.post("/api/v1/auth/register", json=_register_payload("user_b@example.com"))
    token_b = _login(client, email="user_b@example.com").json()["access_token"]

    # User B tries to delete User A's account -> expects 403
    del_b = client.delete(
        f"/api/v1/social-accounts/{account.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_b.status_code == 403

    # User A deletes their own account -> expects 200
    del_a = client.delete(
        f"/api/v1/social-accounts/{account.id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert del_a.status_code == 200
    assert db_session.query(SocialAccount).filter(SocialAccount.id == account.id).first() is None


def test_refresh_token(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload())
    token = _login(client).json()["access_token"]
    user = db_session.query(User).first()

    account = SocialAccount(
        user_id=user.id,
        platform="linkedin",
        provider="linkedin",
        external_account_id="linkedin-a-123",
        account_name="Alice LinkedIn",
        access_token_encrypted=encrypt_token("access-old"),
        refresh_token_encrypted=encrypt_token("refresh-old"),
        status=SocialAccountStatus.CONNECTED,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    # Trigger refresh
    refresh_res = client.post(
        f"/api/v1/social-accounts/{account.id}/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert refresh_res.status_code == 200
    assert refresh_res.json()["status"] == "CONNECTED"

    # Verify token is updated in DB
    db_session.refresh(account)
    assert decrypt_token(account.access_token_encrypted) == "mock-linkedin-refreshed-access-token"


def test_missing_encryption_key_validation(client, db_session: Session):
    # Set to empty to trigger config validation
    old_key = os.environ.get("SOCIAL_TOKEN_ENCRYPTION_KEY")
    os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = ""
    try:
        from app.core.encryption import encrypt_token as test_encrypt
        try:
            test_encrypt("test-token")
            assert False, "Should raise ValueError when key is missing"
        except ValueError as exc:
            assert "SOCIAL_TOKEN_ENCRYPTION_KEY is not configured" in str(exc)
    finally:
        if old_key:
            os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = old_key


def test_oauth_state_is_bound_to_provider(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload("provider-state@example.com"))
    token = _login(client, email="provider-state@example.com").json()["access_token"]
    client.get("/api/v1/social-accounts/meta/connect", headers={"Authorization": f"Bearer {token}"})
    state = db_session.query(OAuthState).one().state

    response = client.get(
        f"/api/v1/social-accounts/linkedin/callback?code=mock-code&state={state}",
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "state_invalid_or_expired" in response.headers["location"]
    assert db_session.query(SocialAccount).count() == 0


def test_expired_and_reused_oauth_states_are_rejected(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload("state-replay@example.com"))
    token = _login(client, email="state-replay@example.com").json()["access_token"]
    client.get("/api/v1/social-accounts/meta/connect", headers={"Authorization": f"Bearer {token}"})
    state = db_session.query(OAuthState).one()
    state.expires_at = state.expires_at.replace(year=2020)
    db_session.commit()

    expired = client.get(
        f"/api/v1/social-accounts/meta/callback?code=mock-code&state={state.state}",
        follow_redirects=False,
    )
    assert "state_invalid_or_expired" in expired.headers["location"]

    client.get("/api/v1/social-accounts/meta/connect", headers={"Authorization": f"Bearer {token}"})
    fresh_state = db_session.query(OAuthState).one().state
    first = client.get(
        f"/api/v1/social-accounts/meta/callback?code=mock-code&state={fresh_state}",
        follow_redirects=False,
    )
    second = client.get(
        f"/api/v1/social-accounts/meta/callback?code=mock-code&state={fresh_state}",
        follow_redirects=False,
    )
    assert first.status_code == 307
    assert second.status_code == 307
    assert "state_invalid_or_expired" in second.headers["location"]


def test_real_mode_requires_configuration_and_generates_provider_url(client):
    old_values = {key: os.environ.get(key) for key in (
        "SOCIAL_MOCK_MODE", "META_CLIENT_ID", "META_CLIENT_SECRET", "META_REDIRECT_URI",
        "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_REDIRECT_URI",
    )}
    try:
        os.environ["SOCIAL_MOCK_MODE"] = "false"
        for key in old_values:
            if key != "SOCIAL_MOCK_MODE":
                os.environ.pop(key, None)
        get_settings.cache_clear()
        client.post("/api/v1/auth/register", json=_register_payload("real-mode@example.com"))
        token = _login(client, email="real-mode@example.com").json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        missing = client.get("/api/v1/social-accounts/meta/connect", headers=headers)
        assert missing.status_code == 502
        assert missing.json()["detail"] == "Meta OAuth is not configured"

        os.environ.update({
            "META_CLIENT_ID": "meta-test-client",
            "META_CLIENT_SECRET": "meta-test-secret",
            "META_REDIRECT_URI": "http://localhost:8000/api/v1/social-accounts/meta/callback",
        })
        get_settings.cache_clear()
        configured = client.get("/api/v1/social-accounts/meta/connect", headers=headers)
        assert configured.status_code == 200
        assert "facebook.com" in configured.json()["url"]
        assert "meta-test-client" in configured.json()["url"]
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()
