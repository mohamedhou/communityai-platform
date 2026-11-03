from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.workspace_context import (
    WorkspaceContext,
    get_workspace_context,
    require_workspace_editor,
)
from app.schemas.business_knowledge import (
    BusinessKnowledgeResponse,
    BusinessKnowledgeUpdate,
    KnowledgeProductCreate,
    KnowledgeProductResponse,
    KnowledgeProductUpdate,
    KnowledgeFAQCreate,
    KnowledgeFAQResponse,
    KnowledgeFAQUpdate,
)
from app.services.business_knowledge_service import BusinessKnowledgeService

router = APIRouter(prefix="/api/v1/business-knowledge", tags=["business-knowledge"])
knowledge_service = BusinessKnowledgeService()


@router.get("", response_model=BusinessKnowledgeResponse)
def get_business_knowledge(
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> BusinessKnowledgeResponse:
    """Retrieve the central business knowledge base for current workspace."""
    knowledge = knowledge_service.get_or_create(db, context.workspace_id)
    return BusinessKnowledgeResponse.model_validate(knowledge)


@router.patch("", response_model=BusinessKnowledgeResponse)
@router.put("", response_model=BusinessKnowledgeResponse)
def update_business_knowledge(
    payload: BusinessKnowledgeUpdate,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> BusinessKnowledgeResponse:
    """Update identity, policies, and editorial guidelines."""
    updated = knowledge_service.update_knowledge(db, context.workspace_id, payload)
    return BusinessKnowledgeResponse.model_validate(updated)


@router.post("/seed-default", response_model=BusinessKnowledgeResponse)
def seed_default_knowledge(
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> BusinessKnowledgeResponse:
    """Seed sample products and FAQs if current knowledge base is empty."""
    knowledge = knowledge_service.get_or_create(db, context.workspace_id)
    knowledge_service.seed_default_items_if_empty(db, context.workspace_id)
    return BusinessKnowledgeResponse.model_validate(knowledge)


# ==========================================
# Products & Services Endpoints
# ==========================================

@router.get("/products", response_model=list[KnowledgeProductResponse])
def list_products(
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[KnowledgeProductResponse]:
    """List products and services in current workspace knowledge base."""
    products = knowledge_service.list_products(db, context.workspace_id)
    return [KnowledgeProductResponse.model_validate(p) for p in products]


@router.post("/products", response_model=KnowledgeProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: KnowledgeProductCreate,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> KnowledgeProductResponse:
    """Add a new product or service."""
    created = knowledge_service.create_product(db, context.workspace_id, payload)
    return KnowledgeProductResponse.model_validate(created)


@router.get("/products/{product_id}", response_model=KnowledgeProductResponse)
def get_product(
    product_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> KnowledgeProductResponse:
    """Get single product details."""
    product = knowledge_service.get_product(db, context.workspace_id, product_id)
    return KnowledgeProductResponse.model_validate(product)


@router.patch("/products/{product_id}", response_model=KnowledgeProductResponse)
@router.put("/products/{product_id}", response_model=KnowledgeProductResponse)
def update_product(
    product_id: int,
    payload: KnowledgeProductUpdate,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> KnowledgeProductResponse:
    """Update a product or service."""
    updated = knowledge_service.update_product(db, context.workspace_id, product_id, payload)
    return KnowledgeProductResponse.model_validate(updated)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a product from the knowledge base."""
    knowledge_service.delete_product(db, context.workspace_id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# FAQs Endpoints
# ==========================================

@router.get("/faqs", response_model=list[KnowledgeFAQResponse])
def list_faqs(
    category: str | None = Query(default=None),
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[KnowledgeFAQResponse]:
    """List FAQs with optional category filter."""
    faqs = knowledge_service.list_faqs(db, context.workspace_id, category=category)
    return [KnowledgeFAQResponse.model_validate(f) for f in faqs]


@router.post("/faqs", response_model=KnowledgeFAQResponse, status_code=status.HTTP_201_CREATED)
def create_faq(
    payload: KnowledgeFAQCreate,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> KnowledgeFAQResponse:
    """Add an official FAQ entry."""
    created = knowledge_service.create_faq(db, context.workspace_id, payload)
    return KnowledgeFAQResponse.model_validate(created)


@router.get("/faqs/{faq_id}", response_model=KnowledgeFAQResponse)
def get_faq(
    faq_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> KnowledgeFAQResponse:
    """Get single FAQ entry."""
    faq = knowledge_service.get_faq(db, context.workspace_id, faq_id)
    return KnowledgeFAQResponse.model_validate(faq)


@router.patch("/faqs/{faq_id}", response_model=KnowledgeFAQResponse)
@router.put("/faqs/{faq_id}", response_model=KnowledgeFAQResponse)
def update_faq(
    faq_id: int,
    payload: KnowledgeFAQUpdate,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> KnowledgeFAQResponse:
    """Update FAQ entry."""
    updated = knowledge_service.update_faq(db, context.workspace_id, faq_id, payload)
    return KnowledgeFAQResponse.model_validate(updated)


@router.delete("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faq(
    faq_id: int,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> Response:
    """Delete FAQ entry."""
    knowledge_service.delete_faq(db, context.workspace_id, faq_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
