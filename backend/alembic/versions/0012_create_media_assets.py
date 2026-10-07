"""create media assets

Revision ID: 0012_create_media_assets
Revises: 0011_content_approval_workflow
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0012_create_media_assets"
down_revision = "0011_content_approval_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        from sqlalchemy.dialects import postgresql

        media_kind = postgresql.ENUM("IMAGE", "VIDEO", name="media_kind", create_type=True)
        media_kind.create(bind, checkfirst=True)
        media_kind_column = postgresql.ENUM("IMAGE", "VIDEO", name="media_kind", create_type=False)
    else:
        media_kind_column = sa.Enum("IMAGE", "VIDEO", name="media_kind")

    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("extension", sa.String(length=10), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("media_kind", media_kind_column, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_media_assets_workspace_id", "media_assets", ["workspace_id"])
    op.create_index("ix_media_assets_uploaded_by", "media_assets", ["uploaded_by"])
    op.create_index("ix_media_assets_storage_key", "media_assets", ["storage_key"], unique=True)
    op.create_index("ix_media_assets_checksum", "media_assets", ["checksum"])
    op.add_column("posts", sa.Column("media_asset_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_posts_media_asset_id", "posts", "media_assets", ["media_asset_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_posts_media_asset_id", "posts", ["media_asset_id"])


def downgrade() -> None:
    op.drop_index("ix_posts_media_asset_id", table_name="posts")
    op.drop_constraint("fk_posts_media_asset_id", "posts", type_="foreignkey")
    op.drop_column("posts", "media_asset_id")
    op.drop_index("ix_media_assets_checksum", table_name="media_assets")
    op.drop_index("ix_media_assets_storage_key", table_name="media_assets")
    op.drop_index("ix_media_assets_uploaded_by", table_name="media_assets")
    op.drop_index("ix_media_assets_workspace_id", table_name="media_assets")
    op.drop_table("media_assets")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="media_kind").drop(bind, checkfirst=True)
