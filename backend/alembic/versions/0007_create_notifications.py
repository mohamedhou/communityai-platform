"""create notifications table

Revision ID: 0007_create_notifications
Revises: 0006_create_analytics_snapshots
Create Date: 2026-09-14 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_create_notifications"
down_revision = "0006_create_analytics_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Create ENUM types explicitly on PostgreSQL
    if bind.dialect.name == "postgresql":
        notification_type_enum = postgresql.ENUM(
            "POST_PUBLISHED",
            "POST_FAILED",
            "POST_SCHEDULED",
            "INBOX_MESSAGE",
            "AI_SUGGESTION",
            "SOCIAL_ACCOUNT",
            "ANALYTICS",
            "SYSTEM",
            name="notification_type",
            create_type=True,
        )
        notification_type_enum.create(bind, checkfirst=True)

        notification_severity_enum = postgresql.ENUM(
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            name="notification_severity",
            create_type=True,
        )
        notification_severity_enum.create(bind, checkfirst=True)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "POST_PUBLISHED",
                "POST_FAILED",
                "POST_SCHEDULED",
                "INBOX_MESSAGE",
                "AI_SUGGESTION",
                "SOCIAL_ACCOUNT",
                "ANALYTICS",
                "SYSTEM",
                name="notification_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "severity",
            postgresql.ENUM(
                "INFO",
                "SUCCESS",
                "WARNING",
                "ERROR",
                name="notification_severity",
                create_type=False,
            ),
            server_default="INFO",
            nullable=False,
        ),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("action_url", sa.String(length=255), nullable=True),
        sa.Column("entity_type", sa.String(length=100), nullable=True),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index("ix_notifications_type", "notifications", ["type"])


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    if bind.dialect.name == "postgresql":
        notification_type_enum = postgresql.ENUM(
            "POST_PUBLISHED",
            "POST_FAILED",
            "POST_SCHEDULED",
            "INBOX_MESSAGE",
            "AI_SUGGESTION",
            "SOCIAL_ACCOUNT",
            "ANALYTICS",
            "SYSTEM",
            name="notification_type",
            create_type=True,
        )
        notification_type_enum.drop(bind, checkfirst=True)

        notification_severity_enum = postgresql.ENUM(
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            name="notification_severity",
            create_type=True,
        )
        notification_severity_enum.drop(bind, checkfirst=True)
