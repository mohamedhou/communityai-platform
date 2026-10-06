"""add content approval workflow to posts

Revision ID: 0011_content_approval_workflow
Revises: 0010_add_workspace_isolation
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0011_content_approval_workflow"
down_revision = "0010_add_workspace_isolation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        from sqlalchemy.dialects import postgresql

        post_approval_status_type = postgresql.ENUM(
            "NOT_REQUIRED",
            "PENDING",
            "APPROVED",
            "REJECTED",
            name="post_approval_status",
            create_type=True,
        )
        post_approval_status_type.create(bind, checkfirst=True)

        post_approval_status = postgresql.ENUM(
            "NOT_REQUIRED",
            "PENDING",
            "APPROVED",
            "REJECTED",
            name="post_approval_status",
            create_type=False,
        )
    else:
        post_approval_status = sa.Enum(
            "NOT_REQUIRED",
            "PENDING",
            "APPROVED",
            "REJECTED",
            name="post_approval_status",
        )

    op.add_column("posts", sa.Column("approval_status", post_approval_status, server_default="NOT_REQUIRED", nullable=False))
    op.add_column("posts", sa.Column("reviewed_by", sa.Integer(), nullable=True))
    op.add_column("posts", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("posts", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("submitted_for_review_at", sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key("fk_posts_reviewed_by", "posts", "users", ["reviewed_by"], ["id"], ondelete="SET NULL")
    op.create_index("ix_posts_workspace_approval", "posts", ["workspace_id", "approval_status"])


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_posts_workspace_approval", table_name="posts")
    op.drop_constraint("fk_posts_reviewed_by", "posts", type_="foreignkey")
    op.drop_column("posts", "submitted_for_review_at")
    op.drop_column("posts", "rejection_reason")
    op.drop_column("posts", "reviewed_at")
    op.drop_column("posts", "reviewed_by")
    op.drop_column("posts", "approval_status")
    if bind.dialect.name == "postgresql":
        sa.Enum(name="post_approval_status").drop(bind, checkfirst=True)
