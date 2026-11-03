from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.business_knowledge import BusinessKnowledge, KnowledgeProduct, KnowledgeFAQ
from app.models.user import User


def _register_and_login(client, email: str, name: str = "Test User"):
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPassword123!", "first_name": name, "last_name": "CM"},
    )
    assert reg_res.status_code == 201
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


def test_business_knowledge_get_or_create(client, db_session: Session):
    _, headers = _register_and_login(client, "bk_user1@example.com", "Alice")

    # Fetch knowledge base
    res = client.get("/api/v1/business-knowledge", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "company_name" in data
    assert "refund_policy" in data
    assert "brand_tone" in data
    assert "Alice" in data["company_name"] or "Workspace" in data["company_name"]


def test_business_knowledge_update(client, db_session: Session):
    _, headers = _register_and_login(client, "bk_user2@example.com", "Bob")

    update_payload = {
        "company_name": "Acme Social Corp",
        "description": "Leader de la relation client augmentée",
        "industry": "Marketing & IA",
        "brand_tone": "innovant, chaleureux et direct",
        "refund_policy": "Remboursement garanti sous 7 jours sans conditions",
        "forbidden_expressions": ["Pas possible", "Débrouillez-vous"],
        "allowed_emojis": ["🚀", "🤝", "💡"],
    }
    patch_res = client.patch("/api/v1/business-knowledge", headers=headers, json=update_payload)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["company_name"] == "Acme Social Corp"
    assert data["refund_policy"] == "Remboursement garanti sous 7 jours sans conditions"
    assert "Pas possible" in data["forbidden_expressions"]
    assert "🚀" in data["allowed_emojis"]


def test_business_knowledge_workspace_isolation(client, db_session: Session):
    """
    CRITICAL TEST: Verifies that Workspace 1 and Workspace 2 have completely
    isolated business knowledge bases, products, and FAQs.
    """
    _, headers_user1 = _register_and_login(client, "ws1_owner@example.com", "Owner One")
    _, headers_user2 = _register_and_login(client, "ws2_owner@example.com", "Owner Two")

    # Workspace 1 sets company name to 'Company Alpha'
    client.patch(
        "/api/v1/business-knowledge",
        headers=headers_user1,
        json={"company_name": "Company Alpha", "refund_policy": "Politique Alpha 100%"},
    )

    # Workspace 2 sets company name to 'Company Beta'
    client.patch(
        "/api/v1/business-knowledge",
        headers=headers_user2,
        json={"company_name": "Company Beta", "refund_policy": "Politique Beta 50%"},
    )

    # Workspace 1 adds a secret product
    prod_res = client.post(
        "/api/v1/business-knowledge/products",
        headers=headers_user1,
        json={
            "name": "Secret Alpha Drone",
            "description": "Technologie confidentielle Alpha",
            "price": "999€",
            "availability": "in_stock",
            "features": ["GPS", "Camera 8K"],
        },
    )
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # Verify Workspace 1 sees its own data
    w1_res = client.get("/api/v1/business-knowledge", headers=headers_user1).json()
    assert w1_res["company_name"] == "Company Alpha"
    assert w1_res["refund_policy"] == "Politique Alpha 100%"

    # Verify Workspace 2 sees only its own data
    w2_res = client.get("/api/v1/business-knowledge", headers=headers_user2).json()
    assert w2_res["company_name"] == "Company Beta"
    assert w2_res["refund_policy"] == "Politique Beta 50%"

    # Verify Workspace 2 cannot see Workspace 1's product
    w2_products = client.get("/api/v1/business-knowledge/products", headers=headers_user2).json()
    assert not any(p["name"] == "Secret Alpha Drone" for p in w2_products)

    # Direct access to Workspace 1 product by Workspace 2 must return 404
    w2_direct_access = client.get(f"/api/v1/business-knowledge/products/{prod_id}", headers=headers_user2)
    assert w2_direct_access.status_code == 404


def test_products_and_faqs_crud(client, db_session: Session):
    _, headers = _register_and_login(client, "crud_user@example.com", "Charlie")

    # 1. Product CRUD
    p_create = client.post(
        "/api/v1/business-knowledge/products",
        headers=headers,
        json={
            "name": "Pack Premium AI",
            "description": "Accès complet aux fonctionnalités",
            "price": "79€ / mois",
            "availability": "in_stock",
            "features": ["Génération illimitée", "Support prioritaire"],
        },
    )
    assert p_create.status_code == 201
    p_id = p_create.json()["id"]

    # Product Update
    p_update = client.patch(
        f"/api/v1/business-knowledge/products/{p_id}",
        headers=headers,
        json={"price": "69€ / mois (Promotion)"},
    )
    assert p_update.status_code == 200
    assert p_update.json()["price"] == "69€ / mois (Promotion)"

    # 2. FAQ CRUD
    faq_create = client.post(
        "/api/v1/business-knowledge/faqs",
        headers=headers,
        json={
            "category": "Tarifs",
            "question": "Existe-t-il un engagement annuel ?",
            "answer": "Non, tous nos forfaits sont sans engagement et résiliables en un clic.",
            "keywords": ["engagement", "résiliation", "contrat", "mensuel"],
            "is_active": True,
        },
    )
    assert faq_create.status_code == 201
    faq_id = faq_create.json()["id"]

    # FAQ List by category
    faqs_list = client.get("/api/v1/business-knowledge/faqs?category=Tarifs", headers=headers)
    assert faqs_list.status_code == 200
    assert len(faqs_list.json()) == 1

    # Product Delete
    p_del = client.delete(f"/api/v1/business-knowledge/products/{p_id}", headers=headers)
    assert p_del.status_code == 204

    # FAQ Delete
    f_del = client.delete(f"/api/v1/business-knowledge/faqs/{faq_id}", headers=headers)
    assert f_del.status_code == 204
