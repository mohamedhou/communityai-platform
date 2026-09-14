"""create user settings table

Revision ID: 0008_create_user_settings
Revises: 0007_create_notifications
Create Date: 2026-09-14 12:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0008_create_user_settings"
down_revision = "0007_create_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("workspace_name", sa.String(length=150), nullable=False),
        sa.Column("workspace_description", sa.String(length=500), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("default_platform", sa.String(length=50), nullable=True),
        sa.Column("notifications_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("post_notifications_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("inbox_notifications_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("social_notifications_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("analytics_notifications_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_settings_user_id"),
    )
    op.create_index(op.f("ix_user_settings_user_id"), "user_settings", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_settings_user_id"), table_name="user_settings")
    op.drop_table("user_settings")