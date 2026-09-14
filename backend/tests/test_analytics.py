from __future__ import annotations

import os
from datetime import date, datetime, timedelta
import pytest
from sqlalchemy.orm import Session

# Set test environment defaults before imports
os.environ["SOCIAL_TOKEN_ENCRYPTION_KEY"] = "G3cZ84fJd9X2-vK8pQLt8G3cZ84fJd9X2-vK8pQLt8E="
os.environ["SOCIAL_MOCK_MODE"] = "true"

from app.core.config import get_settings
from app.core.encryption import encrypt_token
from app.models.analytics_snapshot import AnalyticsSnapshot
from app.models.post import Post, PostStatus
from app.models.user import User
from app.social.models import SocialAccount


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


def _setup_user_and_social(
    client,
    db_session: Session,
    email: str = "alice@example.com",
    platform: str = "facebook",
    provider: str = "meta",
):
    client.post("/api/v1/auth/register", json=_register_payload(email))
    token = _login(client, email=email).json()["access_token"]
    user = db_session.query(User).filter(User.email == email).one()

    account = SocialAccount(
        user_id=user.id,
        platform=platform,
        provider=provider,
        external_account_id=f"{platform}-acc-{user.id}",
        account_name=f"{user.first_name} {platform.title()} Page",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return token, user, account


def test_analytics_unauthenticated(client):
    endpoints = [
        ("GET", "/api/v1/analytics/summary"),
        ("GET", "/api/v1/analytics/timeseries"),
        ("GET", "/api/v1/analytics/top-posts"),
        ("POST", "/api/v1/analytics/seed-mock"),
    ]
    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path)
        assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"


def test_analytics_ownership_and_isolation(client, db_session: Session):
    token_a, user_a, acc_a = _setup_user_and_social(client, db_session, email="owner_a@example.com")
    token_b, user_b, acc_b = _setup_user_and_social(client, db_session, email="intruder_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Seed mock data for User A
    client.post("/api/v1/analytics/seed-mock", headers=headers_a)

    # User B querying User A's social_account_id -> 404
    res_b = client.get(f"/api/v1/analytics/summary?social_account_id={acc_a.id}", headers=headers_b)
    assert res_b.status_code == 404

    res_b_ts = client.get(f"/api/v1/analytics/timeseries?social_account_id={acc_a.id}", headers=headers_b)
    assert res_b_ts.status_code == 404

    res_b_top = client.get(f"/api/v1/analytics/top-posts?social_account_id={acc_a.id}", headers=headers_b)
    assert res_b_top.status_code == 404


def test_analytics_total_followers_is_latest_snapshot(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="followers_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Manually create 3 snapshots with known follower values
    today = date.today()
    s1 = AnalyticsSnapshot(
        user_id=user.id,
        social_account_id=account.id,
        date=today - timedelta(days=2),
        followers=1000,
        follower_growth=10,
        impressions=100,
        reach=80,
        engagement=10,
    )
    s2 = AnalyticsSnapshot(
        user_id=user.id,
        social_account_id=account.id,
        date=today - timedelta(days=1),
        followers=1015,
        follower_growth=15,
        impressions=120,
        reach=90,
        engagement=12,
    )
    s3 = AnalyticsSnapshot(
        user_id=user.id,
        social_account_id=account.id,
        date=today,
        followers=1035,
        follower_growth=20,
        impressions=150,
        reach=100,
        engagement=15,
    )
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    res = client.get("/api/v1/analytics/summary?days=7", headers=headers)
    assert res.status_code == 200
    kpis = res.json()["kpis"]

    # CRITICAL: Total followers must be the latest value (1035), NOT the sum (1000+1015+1035 = 3050)
    assert kpis["total_followers"] == 1035
    # Follower growth must be latest (1035) - earliest (1000) = 35
    assert kpis["follower_growth"] == 35


def test_analytics_multi_account_follower_growth(client, db_session: Session):
    token, user, acc1 = _setup_user_and_social(
        client, db_session, email="multi_acc@example.com", platform="facebook", provider="meta"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Add second social account for user
    acc2 = SocialAccount(
        user_id=user.id,
        platform="linkedin",
        provider="linkedin",
        external_account_id=f"li-acc-{user.id}",
        account_name=f"{user.first_name} LinkedIn Page",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db_session.add(acc2)
    db_session.commit()
    db_session.refresh(acc2)

    today = date.today()
    # Account 1: 100 -> 125 (+25)
    s1_a = AnalyticsSnapshot(user_id=user.id, social_account_id=acc1.id, date=today - timedelta(days=5), followers=100, reach=50, engagement=5)
    s1_b = AnalyticsSnapshot(user_id=user.id, social_account_id=acc1.id, date=today, followers=125, reach=60, engagement=6)

    # Account 2: 200 -> 210 (+10)
    s2_a = AnalyticsSnapshot(user_id=user.id, social_account_id=acc2.id, date=today - timedelta(days=5), followers=200, reach=80, engagement=8)
    s2_b = AnalyticsSnapshot(user_id=user.id, social_account_id=acc2.id, date=today, followers=210, reach=90, engagement=9)

    db_session.add_all([s1_a, s1_b, s2_a, s2_b])
    db_session.commit()

    res = client.get("/api/v1/analytics/summary?days=7", headers=headers)
    assert res.status_code == 200
    data = res.json()
    kpis = data["kpis"]

    # Total followers across both accounts: 125 + 210 = 335
    assert kpis["total_followers"] == 335
    # Total growth: (125 + 210) - (100 + 200) = 335 - 300 = 35
    assert kpis["follower_growth"] == 35
    assert data["accounts_count"] == 2


def test_analytics_engagement_rate_and_zero_division(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="rate_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    today = date.today()
    # Snapshot with 0 reach and 0 engagement
    s_zero = AnalyticsSnapshot(
        user_id=user.id,
        social_account_id=account.id,
        date=today,
        followers=500,
        reach=0,
        impressions=0,
        engagement=0,
    )
    db_session.add(s_zero)
    db_session.commit()

    res = client.get("/api/v1/analytics/summary?days=1", headers=headers)
    assert res.status_code == 200
    kpis = res.json()["kpis"]
    # Zero division handled properly without error
    assert kpis["engagement_rate"] == 0.0

    # Add snapshot with reach=2000 and engagement=100 -> 5.0% rate
    s_zero.reach = 2000
    s_zero.engagement = 100
    db_session.commit()

    res2 = client.get("/api/v1/analytics/summary?days=1", headers=headers)
    assert res2.status_code == 200
    assert res2.json()["kpis"]["engagement_rate"] == 5.0


def test_analytics_date_and_platform_filtering(client, db_session: Session):
    token, user, acc_fb = _setup_user_and_social(
        client, db_session, email="filter_test@example.com", platform="facebook", provider="meta"
    )
    headers = {"Authorization": f"Bearer {token}"}

    acc_li = SocialAccount(
        user_id=user.id,
        platform="linkedin",
        provider="linkedin",
        external_account_id=f"li-acc-{user.id}",
        account_name="Filter Test LinkedIn",
        access_token_encrypted=encrypt_token("mock-token"),
        status="CONNECTED",
    )
    db_session.add(acc_li)
    db_session.commit()
    db_session.refresh(acc_li)

    today = date.today()
    # Facebook snapshot 10 days ago (impressions=1000)
    s_fb_old = AnalyticsSnapshot(user_id=user.id, social_account_id=acc_fb.id, date=today - timedelta(days=10), followers=500, impressions=1000, reach=800, engagement=50)
    # Facebook snapshot today (impressions=2000)
    s_fb_now = AnalyticsSnapshot(user_id=user.id, social_account_id=acc_fb.id, date=today, followers=520, impressions=2000, reach=1500, engagement=100)
    # LinkedIn snapshot today (impressions=500)
    s_li_now = AnalyticsSnapshot(user_id=user.id, social_account_id=acc_li.id, date=today, followers=300, impressions=500, reach=400, engagement=25)

    db_session.add_all([s_fb_old, s_fb_now, s_li_now])
    db_session.commit()

    # Filter by platform=linkedin
    res_li = client.get("/api/v1/analytics/summary?platform=linkedin", headers=headers)
    assert res_li.status_code == 200
    assert res_li.json()["kpis"]["total_impressions"] == 500

    # Filter by platform=facebook and days=3 (should only include s_fb_now)
    res_fb_3d = client.get("/api/v1/analytics/summary?platform=facebook&days=3", headers=headers)
    assert res_fb_3d.status_code == 200
    assert res_fb_3d.json()["kpis"]["total_impressions"] == 2000

    # Timeseries endpoint filtering
    res_ts = client.get("/api/v1/analytics/timeseries?platform=facebook&days=3", headers=headers)
    assert res_ts.status_code == 200
    pts = res_ts.json()["points"]
    assert len(pts) == 1
    assert pts[0]["impressions"] == 2000


def test_analytics_top_posts(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="topposts_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create several published posts
    p1 = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Post 1: Awesome Community Announcement!",
        status=PostStatus.PUBLISHED,
        published_at=datetime.now(),
    )
    p2 = Post(
        user_id=user.id,
        social_account_id=account.id,
        content="Post 2: Tips and Tricks for Social Engagement 🚀",
        status=PostStatus.PUBLISHED,
        published_at=datetime.now(),
    )
    db_session.add_all([p1, p2])
    db_session.commit()

    res = client.get("/api/v1/analytics/top-posts?limit=5", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    items = data["items"]
    # Check that items are sorted descending by engagement
    for i in range(len(items) - 1):
        assert items[i]["engagement"] >= items[i + 1]["engagement"]
        assert items[i]["platform"] == "facebook"


def test_analytics_seed_mock_authorization(client, db_session: Session, monkeypatch):
    token, user, account = _setup_user_and_social(client, db_session, email="seed_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Seed allowed in mock mode
    res_mock = client.post("/api/v1/analytics/seed-mock?days=14", headers=headers)
    assert res_mock.status_code == 201
    assert res_mock.json()["snapshots_created"] > 0

    # Seed forbidden when mock mode is disabled
    settings = get_settings()
    monkeypatch.setattr(settings, "social_mock_mode", False)

    res_nomock = client.post("/api/v1/analytics/seed-mock?days=14", headers=headers)
    assert res_nomock.status_code == 403


def test_analytics_no_tokens_in_responses(client, db_session: Session):
    token, user, account = _setup_user_and_social(client, db_session, email="security_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/analytics/seed-mock", headers=headers)

    res_sum = client.get("/api/v1/analytics/summary", headers=headers).json()
    res_ts = client.get("/api/v1/analytics/timeseries", headers=headers).json()
    res_top = client.get("/api/v1/analytics/top-posts", headers=headers).json()

    for resp in [res_sum, res_ts, res_top]:
        dump = str(resp)
        assert "access_token" not in dump
        assert "access_token_encrypted" not in dump
        assert "refresh_token" not in dump
        assert "refresh_token_encrypted" not in dump
