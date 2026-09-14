"""create analytics snapshots table

Revision ID: 0006_create_analytics_snapshots
Revises: 0005_create_inbox_messages
Create Date: 2026-09-01 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_create_analytics_snapshots"
down_revision = "0005_create_inbox_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("social_account_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("followers", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("follower_growth", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("impressions", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("reach", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("engagement", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("likes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("comments", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("shares", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("clicks", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("posts_published", sa.Integer(), server_default=sa.text("0"), nullable=False),
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

    op.create_index("ix_analytics_snapshots_user_id", "analytics_snapshots", ["user_id"])
    op.create_index("ix_analytics_snapshots_social_account_id", "analytics_snapshots", ["social_account_id"])
    op.create_index("ix_analytics_snapshots_date", "analytics_snapshots", ["date"])


def downgrade() -> None:
    op.drop_index("ix_analytics_snapshots_date", table_name="analytics_snapshots")
    op.drop_index("ix_analytics_snapshots_social_account_id", table_name="analytics_snapshots")
    op.drop_index("ix_analytics_snapshots_user_id", table_name="analytics_snapshots")
    op.drop_table("analytics_snapshots")
