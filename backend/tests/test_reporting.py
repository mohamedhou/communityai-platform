from __future__ import annotations

from datetime import date, timedelta
import os

from sqlalchemy.orm import Session

# Match the existing analytics test environment without exposing real credentials.
os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from app.core.encryption import encrypt_token
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.post import Post, PostStatus
from app.models.user import User
from app.social.models import SocialAccount


def setup_user(client, db_session: Session, email: str) -> tuple[str, User, SocialAccount]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "first_name": "Élodie", "last_name": "Rapport"},
    )
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"}).json()["access_token"]
    user = db_session.query(User).filter(User.email == email).one()
    account = SocialAccount(
        user_id=user.id,
        platform="facebook",
        provider="meta",
        external_account_id=f"report-{user.id}",
        account_name="Élodie Facebook",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return token, user, account


def add_snapshot(db_session: Session, user_id: int, account_id: int, day: date, **values: int) -> None:
    db_session.add(AnalyticsSnapshot(user_id=user_id, social_account_id=account_id, date=day, **values))
    db_session.commit()


def test_reporting_requires_authentication(client):
    query = "?start_date=2026-09-01&end_date=2026-09-14"
    assert client.get(f"/api/v1/reports/preview{query}").status_code == 401
    assert client.get(f"/api/v1/reports/export/csv{query}").status_code == 401
    assert client.get(f"/api/v1/reports/export/pdf{query}").status_code == 401


def test_report_preview_reuses_analytics_values_and_filters(client, db_session: Session):
    token, user, account = setup_user(client, db_session, "report-preview@example.com")
    today = date.today()
    add_snapshot(db_session, user.id, account.id, today - timedelta(days=1), followers=100, reach=200, impressions=300, engagement=20, likes=10, comments=4, shares=3, clicks=3)
    add_snapshot(db_session, user.id, account.id, today, followers=125, reach=250, impressions=400, engagement=25, likes=12, comments=5, shares=4, clicks=4)
    headers = {"Authorization": f"Bearer {token}"}
    query = f"?social_account_id={account.id}&platform=facebook&start_date={today - timedelta(days=1)}&end_date={today}"

    response = client.get(f"/api/v1/reports/preview{query}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    analytics_response = client.get(
        f"/api/v1/analytics/summary?social_account_id={account.id}&platform=facebook&start_date={today - timedelta(days=1)}&end_date={today}",
        headers=headers,
    )
    assert analytics_response.status_code == 200
    assert data["kpis"] == analytics_response.json()["kpis"]
    assert data["workspace_name"] == "Élodie Rapport"
    assert data["period_start"] == str(today - timedelta(days=1))
    assert data["kpis"]["total_followers"] == 125
    assert data["kpis"]["follower_growth"] == 25
    assert data["kpis"]["total_engagement"] == 45
    assert data["engagement_breakdown"]["likes"] == 22
    assert data["accounts"] == ["Élodie Facebook"]
    assert len(data["time_series"]) == 2
    assert "password_hash" not in data
    assert "access_token_encrypted" not in data


def test_reporting_ownership_and_date_validation(client, db_session: Session):
    token_a, user_a, account_a = setup_user(client, db_session, "report-owner@example.com")
    token_b, _, _ = setup_user(client, db_session, "report-other@example.com")
    today = date.today()
    add_snapshot(db_session, user_a.id, account_a.id, today, followers=100, reach=100, engagement=10)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    ownership = client.get(
        f"/api/v1/reports/preview?social_account_id={account_a.id}&start_date={today}&end_date={today}",
        headers=headers_b,
    )
    assert ownership.status_code == 404

    invalid_dates = client.get(
        f"/api/v1/reports/preview?start_date={today}&end_date={today - timedelta(days=1)}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert invalid_dates.status_code == 422

    long_period = client.get(
        f"/api/v1/reports/preview?start_date={today - timedelta(days=366)}&end_date={today}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert long_period.status_code == 422


def test_csv_export_is_utf8_and_contains_report_sections(client, db_session: Session):
    token, user, account = setup_user(client, db_session, "report-csv@example.com")
    today = date.today()
    add_snapshot(db_session, user.id, account.id, today, followers=100, reach=100, engagement=10, likes=5, comments=2, shares=2, clicks=1)
    post = Post(user_id=user.id, social_account_id=account.id, content="Création réussie", status=PostStatus.PUBLISHED)
    db_session.add(post)
    db_session.commit()
    response = client.get(
        f"/api/v1/reports/export/csv?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=\"communityai-report-" in response.headers["content-disposition"]
    assert "REPORT" in response.content.decode("utf-8-sig")
    assert "Création réussie" in response.content.decode("utf-8-sig")
    assert b"password_hash" not in response.content
    assert b"mock-token" not in response.content


def test_pdf_export_is_non_empty_and_does_not_expose_secrets(client, db_session: Session):
    token, user, account = setup_user(client, db_session, "report-pdf@example.com")
    today = date.today()
    add_snapshot(db_session, user.id, account.id, today, followers=100, reach=100, engagement=10)
    response = client.get(
        f"/api/v1/reports/export/pdf?social_account_id={account.id}&start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF-1.4")
    assert len(response.content) > 100
    assert b"password_hash" not in response.content
    assert b"mock-token" not in response.content
