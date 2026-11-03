"""create ai community manager

Revision ID: 0013_create_ai_community_manager
Revises: 0012_create_media_assets
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0013_create_ai_community_manager"
down_revision = "0012_create_media_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        from sqlalchemy.dialects import postgresql

        mode_enum = postgresql.ENUM("MANUAL", "APPROVAL_REQUIRED", "AUTOMATIC", name="aicm_mode", create_type=True)
        mode_enum.create(bind, checkfirst=True)
        mode_col = postgresql.ENUM("MANUAL", "APPROVAL_REQUIRED", "AUTOMATIC", name="aicm_mode", create_type=False)

        status_enum = postgresql.ENUM("SUGGESTED", "APPROVED", "REJECTED", "SENT", "FAILED", name="ai_reply_draft_status", create_type=True)
        status_enum.create(bind, checkfirst=True)
        status_col = postgresql.ENUM("SUGGESTED", "APPROVED", "REJECTED", "SENT", "FAILED", name="ai_reply_draft_status", create_type=False)
    else:
        mode_col = sa.Enum("MANUAL", "APPROVAL_REQUIRED", "AUTOMATIC", name="aicm_mode")
        status_col = sa.Enum("SUGGESTED", "APPROVED", "REJECTED", "SENT", "FAILED", name="ai_reply_draft_status")

    # 1. business_knowledge table
    op.create_table(
        "business_knowledge",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("industry", sa.String(length=150), nullable=False, server_default=""),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=100), nullable=True),
        sa.Column("operating_hours", sa.Text(), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("refund_policy", sa.Text(), nullable=True),
        sa.Column("return_policy", sa.Text(), nullable=True),
        sa.Column("warranty_policy", sa.Text(), nullable=True),
        sa.Column("shipping_policy", sa.Text(), nullable=True),
        sa.Column("complaint_procedure", sa.Text(), nullable=True),
        sa.Column("support_contact", sa.Text(), nullable=True),
        sa.Column("brand_tone", sa.String(length=150), nullable=False, server_default="professionnel, bienveillant et réactif"),
        sa.Column("writing_style", sa.Text(), nullable=True),
        sa.Column("preferred_expressions", sa.JSON(), nullable=False),
        sa.Column("forbidden_expressions", sa.JSON(), nullable=False),
        sa.Column("allowed_emojis", sa.JSON(), nullable=False),
        sa.Column("preferred_languages", sa.JSON(), nullable=False),
        sa.Column("approved_examples", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", name="uq_business_knowledge_workspace_id"),
    )
    op.create_index("ix_business_knowledge_workspace_id", "business_knowledge", ["workspace_id"], unique=True)

    # 2. knowledge_products table
    op.create_table(
        "knowledge_products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("price", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("availability", sa.String(length=100), nullable=False, server_default="in_stock"),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("promotions", sa.Text(), nullable=True),
        sa.Column("delivery_terms", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_knowledge_products_workspace_id", "knowledge_products", ["workspace_id"])
    op.create_index("ix_knowledge_products_name", "knowledge_products", ["name"])

    # 3. knowledge_faqs table
    op.create_table(
        "knowledge_faqs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="Général"),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_knowledge_faqs_workspace_id", "knowledge_faqs", ["workspace_id"])

    # 4. ai_cm_settings table
    op.create_table(
        "ai_cm_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("mode", mode_col, nullable=False),
        sa.Column("enabled_platforms", sa.JSON(), nullable=False),
        sa.Column("allowed_languages", sa.JSON(), nullable=False),
        sa.Column("min_confidence_score", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("auto_reply_intents", sa.JSON(), nullable=False),
        sa.Column("blocked_intents", sa.JSON(), nullable=False),
        sa.Column("working_hours_only", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("working_hours_schedule", sa.JSON(), nullable=True),
        sa.Column("default_escalation_user_id", sa.Integer(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["default_escalation_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("workspace_id", name="uq_ai_cm_settings_workspace_id"),
    )
    op.create_index("ix_ai_cm_settings_workspace_id", "ai_cm_settings", ["workspace_id"], unique=True)

    # 5. ai_reply_drafts table
    op.create_table(
        "ai_reply_drafts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("inbox_message_id", sa.Integer(), nullable=False),
        sa.Column("reply_text", sa.Text(), nullable=False),
        sa.Column("original_reply_text", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.9"),
        sa.Column("sources_used", sa.JSON(), nullable=False),
        sa.Column("status", status_col, nullable=False),
        sa.Column("requires_human", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("created_by_ai", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_reply_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inbox_message_id"], ["inbox_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ai_reply_drafts_workspace_id", "ai_reply_drafts", ["workspace_id"])
    op.create_index("ix_ai_reply_drafts_inbox_message_id", "ai_reply_drafts", ["inbox_message_id"])
    op.create_index("ix_ai_reply_drafts_idempotency_key", "ai_reply_drafts", ["idempotency_key"], unique=True)

    # 6. ai_cm_audit_logs table
    op.create_table(
        "ai_cm_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("inbox_message_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inbox_message_id"], ["inbox_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ai_cm_audit_logs_workspace_id", "ai_cm_audit_logs", ["workspace_id"])
    op.create_index("ix_ai_cm_audit_logs_inbox_message_id", "ai_cm_audit_logs", ["inbox_message_id"])
    op.create_index("ix_ai_cm_audit_logs_user_id", "ai_cm_audit_logs", ["user_id"])
    op.create_index("ix_ai_cm_audit_logs_created_at", "ai_cm_audit_logs", ["created_at"])

    # 7. Add columns to inbox_messages
    op.add_column("inbox_messages", sa.Column("intent", sa.String(length=100), nullable=True))
    op.add_column("inbox_messages", sa.Column("urgency", sa.String(length=50), nullable=True, server_default="normal"))
    op.add_column("inbox_messages", sa.Column("topic", sa.String(length=150), nullable=True))
    op.add_column("inbox_messages", sa.Column("language", sa.String(length=10), nullable=True))
    op.add_column("inbox_messages", sa.Column("ai_analysis", sa.JSON(), nullable=True))
    op.add_column("inbox_messages", sa.Column("assigned_to_user_id", sa.Integer(), nullable=True))
    op.add_column("inbox_messages", sa.Column("is_escalated", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("inbox_messages", sa.Column("escalated_to_user_id", sa.Integer(), nullable=True))
    op.add_column("inbox_messages", sa.Column("escalation_note", sa.Text(), nullable=True))
    op.add_column("inbox_messages", sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_inbox_messages_intent", "inbox_messages", ["intent"])
    op.create_index("ix_inbox_messages_urgency", "inbox_messages", ["urgency"])
    op.create_index("ix_inbox_messages_assigned_to_user_id", "inbox_messages", ["assigned_to_user_id"])
    op.create_index("ix_inbox_messages_is_escalated", "inbox_messages", ["is_escalated"])
    op.create_index("ix_inbox_messages_escalated_to_user_id", "inbox_messages", ["escalated_to_user_id"])

    op.create_foreign_key(
        "fk_inbox_messages_assigned_to_user_id",
        "inbox_messages",
        "users",
        ["assigned_to_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_inbox_messages_escalated_to_user_id",
        "inbox_messages",
        "users",
        ["escalated_to_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    op.drop_constraint("fk_inbox_messages_escalated_to_user_id", "inbox_messages", type_="foreignkey")
    op.drop_constraint("fk_inbox_messages_assigned_to_user_id", "inbox_messages", type_="foreignkey")
    op.drop_index("ix_inbox_messages_escalated_to_user_id", table_name="inbox_messages")
    op.drop_index("ix_inbox_messages_is_escalated", table_name="inbox_messages")
    op.drop_index("ix_inbox_messages_assigned_to_user_id", table_name="inbox_messages")
    op.drop_index("ix_inbox_messages_urgency", table_name="inbox_messages")
    op.drop_index("ix_inbox_messages_intent", table_name="inbox_messages")

    op.drop_column("inbox_messages", "escalated_at")
    op.drop_column("inbox_messages", "escalation_note")
    op.drop_column("inbox_messages", "escalated_to_user_id")
    op.drop_column("inbox_messages", "is_escalated")
    op.drop_column("inbox_messages", "assigned_to_user_id")
    op.drop_column("inbox_messages", "ai_analysis")
    op.drop_column("inbox_messages", "language")
    op.drop_column("inbox_messages", "topic")
    op.drop_column("inbox_messages", "urgency")
    op.drop_column("inbox_messages", "intent")

    op.drop_index("ix_ai_cm_audit_logs_created_at", table_name="ai_cm_audit_logs")
    op.drop_index("ix_ai_cm_audit_logs_user_id", table_name="ai_cm_audit_logs")
    op.drop_index("ix_ai_cm_audit_logs_inbox_message_id", table_name="ai_cm_audit_logs")
    op.drop_index("ix_ai_cm_audit_logs_workspace_id", table_name="ai_cm_audit_logs")
    op.drop_table("ai_cm_audit_logs")

    op.drop_index("ix_ai_reply_drafts_idempotency_key", table_name="ai_reply_drafts")
    op.drop_index("ix_ai_reply_drafts_inbox_message_id", table_name="ai_reply_drafts")
    op.drop_index("ix_ai_reply_drafts_workspace_id", table_name="ai_reply_drafts")
    op.drop_table("ai_reply_drafts")

    op.drop_index("ix_ai_cm_settings_workspace_id", table_name="ai_cm_settings")
    op.drop_table("ai_cm_settings")

    op.drop_index("ix_knowledge_faqs_workspace_id", table_name="knowledge_faqs")
    op.drop_table("knowledge_faqs")

    op.drop_index("ix_knowledge_products_name", table_name="knowledge_products")
    op.drop_index("ix_knowledge_products_workspace_id", table_name="knowledge_products")
    op.drop_table("knowledge_products")

    op.drop_index("ix_business_knowledge_workspace_id", table_name="business_knowledge")
    op.drop_table("business_knowledge")

    if is_postgres:
        sa.Enum(name="ai_reply_draft_status").drop(bind, checkfirst=True)
        sa.Enum(name="aicm_mode").drop(bind, checkfirst=True)
