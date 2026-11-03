from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class BusinessKnowledge(Base):
    """
    Central business knowledge base for a workspace.
    Contains company identity, customer service policies, and editorial guidelines.
    """
    __tablename__ = "business_knowledge"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 1. Company Identity
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    industry: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    operating_hours: Mapped[str | None] = mapped_column(Text, nullable=True)
    languages: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["fr"], nullable=False)

    # 2. Customer Service Policies
    refund_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    return_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    warranty_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    complaint_procedure: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_contact: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 3. Editorial Identity & Voice
    brand_tone: Mapped[str] = mapped_column(String(150), default="professionnel, bienveillant et réactif", nullable=False)
    writing_style: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_expressions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    forbidden_expressions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    allowed_emojis: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_languages: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["fr"], nullable=False)
    approved_examples: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    workspace = relationship("Workspace")


class KnowledgeProduct(Base):
    """
    Products and services catalogue associated with the workspace knowledge base.
    """
    __tablename__ = "knowledge_products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    availability: Mapped[str] = mapped_column(String(100), default="in_stock", nullable=False)  # in_stock, out_of_stock, preorder, on_demand
    features: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    promotions: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    workspace = relationship("Workspace")


class KnowledgeFAQ(Base):
    """
    Frequently Asked Questions catalogue for customer inquiries.
    """
    __tablename__ = "knowledge_faqs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(String(100), default="Général", nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Text] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    workspace = relationship("Workspace")
