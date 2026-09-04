"""create inbox messages table

Revision ID: 0005_create_inbox_messages
Revises: 0004_create_posts
Create Date: 2026-08-25 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_create_inbox_messages"
down_revision = "0004_create_posts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Create ENUM types explicitly on PostgreSQL
    if bind.dialect.name == "postgresql":
        inbox_type_enum = postgresql.ENUM(
            "COMMENT",
            "MESSAGE",
            "MENTION",
            name="inbox_message_type",
            create_type=True,
        )
        inbox_type_enum.create(bind, checkfirst=True)

        inbox_sentiment_enum = postgresql.ENUM(
            "POSITIVE",
            "NEUTRAL",
            "NEGATIVE",
            "UNKNOWN",
            name="inbox_sentiment",
            create_type=True,
        )
        inbox_sentiment_enum.create(bind, checkfirst=True)

    op.create_table(
        "inbox_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("social_account_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "COMMENT",
                "MESSAGE",
                "MENTION",
                name="inbox_message_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("sender_name", sa.String(length=255), nullable=False),
        sa.Column("sender_external_id", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "sentiment",
            postgresql.ENUM(
                "POSITIVE",
                "NEUTRAL",
                "NEGATIVE",
                "UNKNOWN",
                name="inbox_sentiment",
                create_type=False,
            ),
            server_default="UNKNOWN",
            nullable=False,
        ),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["social_account_id"], ["social_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_inbox_messages_user_id", "inbox_messages", ["user_id"])
    op.create_index("ix_inbox_messages_social_account_id", "inbox_messages", ["social_account_id"])


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_inbox_messages_social_account_id", table_name="inbox_messages")
    op.drop_index("ix_inbox_messages_user_id", table_name="inbox_messages")
    op.drop_table("inbox_messages")

    if bind.dialect.name == "postgresql":
        inbox_type_enum = postgresql.ENUM(
            "COMMENT",
            "MESSAGE",
            "MENTION",
            name="inbox_message_type",
            create_type=True,
        )
        inbox_type_enum.drop(bind, checkfirst=True)

        inbox_sentiment_enum = postgresql.ENUM(
            "POSITIVE",
            "NEUTRAL",
            "NEGATIVE",
            "UNKNOWN",
            name="inbox_sentiment",
            create_type=True,
        )
        inbox_sentiment_enum.drop(bind, checkfirst=True)
