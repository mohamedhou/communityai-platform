from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole


def _register_payload(email: str = "user@example.com", first: str = "John") -> dict[str, str]:
    return {
        "email": email,
        "password": "StrongPass123",
        "first_name": first,
        "last_name": "Doe",
    }


def _login(client, email: str = "user@example.com", password: str = "StrongPass123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_get_me_success(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    login_res = _login(client)
    token = login_res.json()["access_token"]

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["first_name"] == "John"
    assert body["role"] == "COMMUNITY_MANAGER"


def test_get_me_unauthenticated(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_put_me_success(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload())
    token = _login(client).json()["access_token"]

    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "Johnny", "last_name": "Smith"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["first_name"] == "Johnny"
    assert body["last_name"] == "Smith"

    user = db_session.query(User).filter(User.email == "user@example.com").one()
    assert user.first_name == "Johnny"
    assert user.last_name == "Smith"


def test_change_password_success(client, db_session: Session):
    client.post("/api/v1/auth/register", json=_register_payload())
    login_res = _login(client)
    token = login_res.json()["access_token"]
    refresh_token = login_res.json()["refresh_token"]

    # Verify refresh token is valid in database
    token_row = db_session.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(refresh_token)).one()
    assert token_row.revoked is False

    response = client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "StrongPass123", "new_password": "NewStrongPass999"},
    )
    assert response.status_code == 200

    # Old login should fail
    assert _login(client, password="StrongPass123").status_code == 401

    # New login should succeed immediately (unique due to jti UUID claim)
    assert _login(client, password="NewStrongPass999").status_code == 200

    # Refresh tokens should be revoked
    db_session.refresh(token_row)
    assert token_row.revoked is True


def test_change_password_invalid_current(client):
    client.post("/api/v1/auth/register", json=_register_payload())
    token = _login(client).json()["access_token"]

    response = client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "WrongPassword", "new_password": "NewStrongPass999"},
    )
    assert response.status_code == 400


def test_admin_list_users(client, db_session: Session):
    # Setup Admin
    client.post("/api/v1/auth/register", json=_register_payload("admin@example.com"))
    admin = db_session.query(User).filter(User.email == "admin@example.com").one()
    admin.role = UserRole.ADMIN
    db_session.commit()
    admin_token = _login(client, email="admin@example.com").json()["access_token"]

    # Setup normal user
    client.post("/api/v1/auth/register", json=_register_payload("normal@example.com"))

    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    emails = [u["email"] for u in body]
    assert "admin@example.com" in emails
    assert "normal@example.com" in emails


def test_client_cannot_list_users(client, db_session: Session):
    # Setup Client
    client.post("/api/v1/auth/register", json=_register_payload("client@example.com"))
    user = db_session.query(User).filter(User.email == "client@example.com").one()
    user.role = UserRole.CLIENT
    db_session.commit()
    client_token = _login(client, email="client@example.com").json()["access_token"]

    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {client_token}"})
    assert response.status_code == 403


def test_admin_get_and_update_user(client, db_session: Session):
    # Setup Admin
    client.post("/api/v1/auth/register", json=_register_payload("admin@example.com"))
    admin = db_session.query(User).filter(User.email == "admin@example.com").one()
    admin.role = UserRole.ADMIN
    db_session.commit()
    admin_token = _login(client, email="admin@example.com").json()["access_token"]

    # Setup target user
    client.post("/api/v1/auth/register", json=_register_payload("target@example.com", "Bob"))
    target = db_session.query(User).filter(User.email == "target@example.com").one()

    # Get target user
    get_res = client.get(f"/api/v1/users/{target.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get_res.status_code == 200
    assert get_res.json()["first_name"] == "Bob"

    # Update target user
    put_res = client.put(
        f"/api/v1/users/{target.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"first_name": "Bobby", "last_name": "Dole"},
    )
    assert put_res.status_code == 200
    assert put_res.json()["first_name"] == "Bobby"


def test_admin_change_role(client, db_session: Session):
    # Setup Admin
    client.post("/api/v1/auth/register", json=_register_payload("admin@example.com"))
    admin = db_session.query(User).filter(User.email == "admin@example.com").one()
    admin.role = UserRole.ADMIN
    db_session.commit()
    admin_token = _login(client, email="admin@example.com").json()["access_token"]

    # Setup target user
    client.post("/api/v1/auth/register", json=_register_payload("target@example.com"))
    target = db_session.query(User).filter(User.email == "target@example.com").one()
    assert target.role == UserRole.COMMUNITY_MANAGER

    response = client.patch(
        f"/api/v1/users/{target.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "CLIENT"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "CLIENT"

    db_session.refresh(target)
    assert target.role == UserRole.CLIENT


def test_admin_cannot_change_own_role(client, db_session: Session):
    # Setup Admin
    client.post("/api/v1/auth/register", json=_register_payload("admin@example.com"))
    admin = db_session.query(User).filter(User.email == "admin@example.com").one()
    admin.role = UserRole.ADMIN
    db_session.commit()
    admin_token = _login(client, email="admin@example.com").json()["access_token"]

    response = client.patch(
        f"/api/v1/users/{admin.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "CLIENT"},
    )
    assert response.status_code == 400


def test_admin_deactivate_user(client, db_session: Session):
    # Setup Admin
    client.post("/api/v1/auth/register", json=_register_payload("admin@example.com"))
    admin = db_session.query(User).filter(User.email == "admin@example.com").one()
    admin.role = UserRole.ADMIN
    db_session.commit()
    admin_token = _login(client, email="admin@example.com").json()["access_token"]

    # Setup target user
    client.post("/api/v1/auth/register", json=_register_payload("target@example.com"))
    target_login = _login(client, email="target@example.com")
    target_access_token = target_login.json()["access_token"]
    target_refresh_token = target_login.json()["refresh_token"]

    target = db_session.query(User).filter(User.email == "target@example.com").one()
    refresh_token_row = (
        db_session.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(target_refresh_token)).one()
    )
    assert refresh_token_row.revoked is False

    # Deactivate user
    deactivate_res = client.patch(
        f"/api/v1/users/{target.id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": False},
    )
    assert deactivate_res.status_code == 200
    assert deactivate_res.json()["is_active"] is False

    # Refresh tokens should be revoked
    db_session.refresh(refresh_token_row)
    assert refresh_token_row.revoked is True

    # User access token should fail immediately on protected routes
    me_res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {target_access_token}"})
    assert me_res.status_code == 401


def test_admin_cannot_deactivate_self(client, db_session: Session):
    # Setup Admin
    client.post("/api/v1/auth/register", json=_register_payload("admin@example.com"))
    admin = db_session.query(User).filter(User.email == "admin@example.com").one()
    admin.role = UserRole.ADMIN
    db_session.commit()
    admin_token = _login(client, email="admin@example.com").json()["access_token"]

    response = client.patch(
        f"/api/v1/users/{admin.id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": False},
    )
    assert response.status_code == 400


def test_consecutive_logins_generate_unique_tokens(client):
    client.post("/api/v1/auth/register", json=_register_payload())

    # Perform two logins in immediate succession (same second)
    res_1 = _login(client)
    res_2 = _login(client)

    assert res_1.status_code == 200
    assert res_2.status_code == 200

    token_1 = res_1.json()["refresh_token"]
    token_2 = res_2.json()["refresh_token"]

    # Verify that the generated tokens and their hashes are different
    assert token_1 != token_2

