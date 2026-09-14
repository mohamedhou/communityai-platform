from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_settings import UserSettings


def register_and_login(client, email: str, password: str = "StrongPass123") -> tuple[str, User]:
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Settings",
            "last_name": "User",
        },
    )
    assert register.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"], User(email=email)


def test_settings_requires_authentication(client):
    assert client.get("/api/v1/settings").status_code == 401
    assert client.patch("/api/v1/settings", json={}).status_code == 401
    assert client.post("/api/v1/settings/change-password", json={}).status_code == 401


def test_get_default_settings_and_no_sensitive_data(client, db_session: Session):
    token, _ = register_and_login(client, "settings-default@example.com")
    response = client.get("/api/v1/settings", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["workspace_name"] == "My Workspace"
    assert data["timezone"] == "UTC"
    assert data["language"] == "en"
    assert data["notifications_enabled"] is True
    assert "password_hash" not in data
    assert "access_token" not in data
    assert "refresh_token" not in data
    assert "access_token_encrypted" not in data
    assert db_session.query(UserSettings).count() == 1


def test_update_settings_persists_across_requests(client):
    token, _ = register_and_login(client, "settings-update@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "first_name": "Updated",
        "last_name": "Manager",
        "workspace_name": "Acme Studio",
        "workspace_description": "Social publishing workspace",
        "timezone": "Europe/Paris",
        "language": "fr",
        "default_platform": "linkedin",
        "notifications_enabled": False,
        "post_notifications_enabled": False,
        "inbox_notifications_enabled": True,
        "social_notifications_enabled": False,
        "analytics_notifications_enabled": True,
    }

    updated = client.patch("/api/v1/settings", headers=headers, json=payload)
    assert updated.status_code == 200
    assert updated.json()["first_name"] == "Updated"
    assert updated.json()["workspace_name"] == "Acme Studio"
    assert updated.json()["notifications_enabled"] is False

    loaded = client.get("/api/v1/settings", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["timezone"] == "Europe/Paris"
    assert loaded.json()["language"] == "fr"
    assert loaded.json()["default_platform"] == "linkedin"


def test_invalid_settings_values_are_rejected(client):
    token, _ = register_and_login(client, "settings-invalid@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    assert client.patch("/api/v1/settings", headers=headers, json={"timezone": "Not/A_Timezone"}).status_code == 422
    assert client.patch("/api/v1/settings", headers=headers, json={"language": "de"}).status_code == 422
    assert client.patch("/api/v1/settings", headers=headers, json={"default_platform": "unknown"}).status_code == 422
    assert client.patch("/api/v1/settings", headers=headers, json={"workspace_name": ""}).status_code == 422


def test_settings_are_isolated_to_authenticated_user(client):
    token_one, _ = register_and_login(client, "settings-one@example.com")
    token_two, _ = register_and_login(client, "settings-two@example.com")
    headers_one = {"Authorization": f"Bearer {token_one}"}
    headers_two = {"Authorization": f"Bearer {token_two}"}

    client.patch("/api/v1/settings", headers=headers_one, json={"workspace_name": "Private One"})
    response_two = client.get("/api/v1/settings", headers=headers_two)

    assert response_two.status_code == 200
    assert response_two.json()["workspace_name"] == "My Workspace"
    assert response_two.json()["workspace_name"] != "Private One"


def test_change_password_success_revokes_sessions_and_old_password_fails(client, db_session: Session):
    old_password = "StrongPass123"
    new_password = "NewStrongPass123"
    email = "settings-password@example.com"
    token, _ = register_and_login(client, email, old_password)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/settings/change-password",
        headers=headers,
        json={"current_password": old_password, "new_password": new_password, "confirm_password": new_password},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": old_password})
    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": new_password})
    assert old_login.status_code == 401
    assert new_login.status_code == 200
    assert db_session.query(User).filter(User.email == email).one().password_hash not in response.text


def test_change_password_validates_current_password_and_confirmation(client):
    token, _ = register_and_login(client, "settings-password-errors@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    wrong_current = client.post(
        "/api/v1/settings/change-password",
        headers=headers,
        json={"current_password": "WrongPass123", "new_password": "NewStrong123", "confirm_password": "NewStrong123"},
    )
    assert wrong_current.status_code == 400

    mismatch = client.post(
        "/api/v1/settings/change-password",
        headers=headers,
        json={"current_password": "StrongPass123", "new_password": "NewStrong123", "confirm_password": "Different123"},
    )
    assert mismatch.status_code == 422

    invalid_new = client.post(
        "/api/v1/settings/change-password",
        headers=headers,
        json={"current_password": "StrongPass123", "new_password": "short", "confirm_password": "short"},
    )
    assert invalid_new.status_code == 422
