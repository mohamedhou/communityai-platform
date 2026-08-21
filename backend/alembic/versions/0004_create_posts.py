"""create posts table

Revision ID: 0004_create_posts
Revises: 0003_create_social_accounts
Create Date: 2026-08-21 18:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_create_posts"
down_revision = "0003_create_social_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Création explicite du type ENUM avec postgresql.ENUM
    if bind.dialect.name == "postgresql":
        post_status_enum = postgresql.ENUM(
            "DRAFT",
            "SCHEDULED",
            "PUBLISHING",
            "PUBLISHED",
            "FAILED",
            "CANCELLED",
            name="post_status",
            create_type=True,
        )
        post_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("social_account_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("media_url", sa.String(length=2048), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "DRAFT",
                "SCHEDULED",
                "PUBLISHING",
                "PUBLISHED",
                "FAILED",
                "CANCELLED",
                name="post_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("external_post_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("posts")

    post_status = postgresql.ENUM(
        "DRAFT",
        "SCHEDULED",
        "PUBLISHING",
        "PUBLISHED",
        "FAILED",
        "CANCELLED",
        name="post_status",
        create_type=True,
    )
    post_status.drop(bind, checkfirst=True)
