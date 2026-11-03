from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ApprovedExample(BaseModel):
    scenario: str = Field(description="Context or topic, e.g. 'Demande de délai de livraison'")
    customer_message: str = Field(description="Typical customer inquiry")
    approved_reply: str = Field(description="Ideal brand reply")


class BusinessKnowledgeBase(BaseModel):
    # Company Identity
    company_name: str = Field(default="", max_length=255)
    description: str = Field(default="")
    industry: str = Field(default="", max_length=150)
    website: str | None = Field(default=None, max_length=255)
    address: str | None = None
    contact_email: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=100)
    operating_hours: str | None = None
    languages: list[str] = Field(default_factory=lambda: ["fr"])

    # Customer Service Policies
    refund_policy: str | None = None
    return_policy: str | None = None
    warranty_policy: str | None = None
    shipping_policy: str | None = None
    complaint_procedure: str | None = None
    support_contact: str | None = None

    # Editorial Guidelines
    brand_tone: str = Field(default="professionnel, bienveillant et réactif", max_length=150)
    writing_style: str | None = None
    preferred_expressions: list[str] = Field(default_factory=list)
    forbidden_expressions: list[str] = Field(default_factory=list)
    allowed_emojis: list[str] = Field(default_factory=list)
    preferred_languages: list[str] = Field(default_factory=lambda: ["fr"])
    approved_examples: list[ApprovedExample] = Field(default_factory=list)


class BusinessKnowledgeUpdate(BaseModel):
    company_name: str | None = None
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    address: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_hours: str | None = None
    languages: list[str] | None = None

    refund_policy: str | None = None
    return_policy: str | None = None
    warranty_policy: str | None = None
    shipping_policy: str | None = None
    complaint_procedure: str | None = None
    support_contact: str | None = None

    brand_tone: str | None = None
    writing_style: str | None = None
    preferred_expressions: list[str] | None = None
    forbidden_expressions: list[str] | None = None
    allowed_emojis: list[str] | None = None
    preferred_languages: list[str] | None = None
    approved_examples: list[ApprovedExample] | None = None


class BusinessKnowledgeResponse(BusinessKnowledgeBase):
    id: int
    workspace_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Product Schemas
# ==========================================

class KnowledgeProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="")
    price: str = Field(default="", max_length=100)
    availability: str = Field(default="in_stock", max_length=100)  # in_stock, out_of_stock, preorder, on_demand
    features: list[str] = Field(default_factory=list)
    promotions: str | None = None
    delivery_terms: str | None = None


class KnowledgeProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    price: str | None = Field(default=None, max_length=100)
    availability: str | None = Field(default=None, max_length=100)
    features: list[str] | None = None
    promotions: str | None = None
    delivery_terms: str | None = None


class KnowledgeProductResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: str
    price: str
    availability: str
    features: list[str]
    promotions: str | None = None
    delivery_terms: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# FAQ Schemas
# ==========================================

class KnowledgeFAQCreate(BaseModel):
    category: str = Field(default="Général", max_length=100)
    question: str = Field(min_length=3)
    answer: str = Field(min_length=2)
    keywords: list[str] = Field(default_factory=list)
    is_active: bool = True


class KnowledgeFAQUpdate(BaseModel):
    category: str | None = Field(default=None, max_length=100)
    question: str | None = None
    answer: str | None = None
    keywords: list[str] | None = None
    is_active: bool | None = None


class KnowledgeFAQResponse(BaseModel):
    id: int
    workspace_id: int
    category: str
    question: str
    answer: str
    keywords: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
