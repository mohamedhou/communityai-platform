"""create social accounts table

Revision ID: 0003_create_social_accounts
Revises: 0002_create_auth_tables
Create Date: 2026-08-19 15:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_create_social_accounts"
down_revision = "0002_create_auth_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Création explicite du type ENUM avec postgresql.ENUM
    if bind.dialect.name == "postgresql":
        social_account_status_enum = postgresql.ENUM(
            "CONNECTED",
            "EXPIRED",
            "REVOKED",
            "ERROR",
            name="social_account_status",
            create_type=True,
        )
        social_account_status_enum.create(bind, checkfirst=True)


    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_account_id", sa.String(length=255), nullable=False),
        sa.Column("account_name", sa.String(length=255), nullable=False),
        sa.Column("account_username", sa.String(length=255), nullable=True),
        sa.Column("profile_image_url", sa.String(length=1024), nullable=True),
        sa.Column("access_token_encrypted", sa.String(length=1024), nullable=False),
        sa.Column("refresh_token_encrypted", sa.String(length=1024), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.String(length=1024), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "CONNECTED",
                "EXPIRED",
                "REVOKED",
                "ERROR",
                name="social_account_status",
                create_type=False,
            ),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_social_accounts_user_id"),
        "social_accounts",
        ["user_id"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_social_accounts_platform_external_id",
        "social_accounts",
        ["user_id", "platform", "external_account_id"],
    )

    op.create_table(
        "oauth_states",
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("state"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("oauth_states")
    op.drop_index(op.f("ix_social_accounts_user_id"), table_name="social_accounts")
    op.drop_table("social_accounts")

    social_account_status = postgresql.ENUM(
        "CONNECTED",
        "EXPIRED",
        "REVOKED",
        "ERROR",
        name="social_account_status",
        create_type=True,
    )
    social_account_status.drop(bind, checkfirst=True)
