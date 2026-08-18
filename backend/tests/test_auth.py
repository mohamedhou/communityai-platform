from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_token
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole


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


def test_register_success(client):
    response = client.post("/api/v1/auth/register", json=_register_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "COMMUNITY_MANAGER"
    assert body["is_active"] is True


def test_register_duplicate_email(client):
    client.post("/api/v1/auth/register", json=_register_payload())

    duplicate_response = client.post("/api/v1/auth/register", json=_register_payload())
    assert duplicate_response.status_code == 409


def test_register_invalid_payload(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "123", "first_name": "", "last_name": ""},
    )
    assert response.status_code == 422


def test_login_success(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    response = _login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    response = _login(client, password="WrongPass123")
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = _login(client, email="missing@example.com")
    assert response.status_code == 401


def test_access_token_valid_for_me(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    login_response = _login(client)
    access_token = login_response.json()["access_token"]

    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "alice@example.com"


def test_access_token_expired(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload())
    user = db_session.query(User).filter(User.email == "alice@example.com").one()

    settings = get_settings()
    expired_token = jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role.value,
            "type": "access",
            "iat": int((datetime.now(UTC) - timedelta(minutes=31)).timestamp()),
            "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401


def test_refresh_valid(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    login_response = _login(client)
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]


def test_refresh_expired(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload())
    user = db_session.query(User).filter(User.email == "alice@example.com").one()

    settings = get_settings()
    expired_refresh = jwt.encode(
        {
            "sub": str(user.id),
            "type": "refresh",
            "iat": int((datetime.now(UTC) - timedelta(days=10)).timestamp()),
            "exp": int((datetime.now(UTC) - timedelta(days=1)).timestamp()),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": expired_refresh})
    assert response.status_code == 401


def test_refresh_wrong_token_type(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    login_response = _login(client)
    access_token = login_response.json()["access_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_protected_route_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_route_invalid_token(client):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert response.status_code == 401


def test_rbac_admin_allowed(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload("admin@example.com"))
    user = db_session.query(User).filter(User.email == "admin@example.com").one()
    user.role = UserRole.ADMIN
    db_session.add(user)
    db_session.commit()

    login_response = _login(client, email="admin@example.com")
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/admin-check",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


def test_rbac_client_forbidden_on_admin_route(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload("client@example.com"))
    user = db_session.query(User).filter(User.email == "client@example.com").one()
    user.role = UserRole.CLIENT
    db_session.add(user)
    db_session.commit()

    login_response = _login(client, email="client@example.com")
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/admin-check",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403


def test_logout_revokes_refresh_token(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload())
    login_response = _login(client)
    refresh_token = login_response.json()["refresh_token"]

    refresh_before_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_before_logout.status_code == 200

    logout_response = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 200

    token_row = db_session.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(refresh_token)).one()
    assert token_row.revoked is True

    refresh_after_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_after_logout.status_code == 401
