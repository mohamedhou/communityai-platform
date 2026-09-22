"""create workspace collaboration tables

Revision ID: 0009_create_workspaces
Revises: 0008_create_user_settings
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_create_workspaces"
down_revision = "0008_create_user_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        from sqlalchemy.dialects import postgresql

        workspace_role_type = postgresql.ENUM(
            "OWNER", "ADMIN", "COMMUNITY_MANAGER", "CLIENT", name="workspace_role", create_type=True
        )
        membership_status_type = postgresql.ENUM("ACTIVE", "INACTIVE", name="membership_status", create_type=True)
        workspace_role_type.create(bind, checkfirst=True)
        membership_status_type.create(bind, checkfirst=True)
        op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'WORKSPACE';")

        workspace_role = postgresql.ENUM(
            "OWNER", "ADMIN", "COMMUNITY_MANAGER", "CLIENT", name="workspace_role", create_type=False
        )
        membership_status = postgresql.ENUM("ACTIVE", "INACTIVE", name="membership_status", create_type=False)
    else:
        workspace_role = sa.Enum("OWNER", "ADMIN", "COMMUNITY_MANAGER", "CLIENT", name="workspace_role")
        membership_status = sa.Enum("ACTIVE", "INACTIVE", name="membership_status")

    op.create_table(
        "workspaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(180), nullable=False, unique=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)
    op.create_table(
        "workspace_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", workspace_role, nullable=False),
        sa.Column("status", membership_status, server_default="ACTIVE", nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member_user"),
    )
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])
    op.create_table(
        "workspace_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", workspace_role, nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invited_by", sa.Integer(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_workspace_invitations_workspace_id", "workspace_invitations", ["workspace_id"])
    op.create_index("ix_workspace_invitations_email", "workspace_invitations", ["email"])
    op.create_index("ix_workspace_invitations_token_hash", "workspace_invitations", ["token_hash"], unique=True)
    op.create_table(
        "workspace_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("event", sa.String(80), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_workspace_activities_workspace_id", "workspace_activities", ["workspace_id"])
    op.create_index("ix_workspace_activities_event", "workspace_activities", ["event"])

    op.execute(
        "INSERT INTO workspaces (name, slug, owner_id) "
        "SELECT COALESCE(s.workspace_name, u.first_name || '''s Workspace', 'My Workspace'), "
        "'user-' || u.id, u.id FROM users u LEFT JOIN user_settings s ON s.user_id = u.id"
    )
    op.execute(
        "INSERT INTO workspace_members (workspace_id, user_id, role, status, joined_at) "
        "SELECT w.id, w.owner_id, 'OWNER', 'ACTIVE', CURRENT_TIMESTAMP FROM workspaces w"
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("workspace_activities")
    op.drop_table("workspace_invitations")
    op.drop_table("workspace_members")
    op.drop_index("ix_workspaces_slug", table_name="workspaces")
    op.drop_table("workspaces")
    if bind.dialect.name == "postgresql":
        sa.Enum(name="membership_status").drop(bind, checkfirst=True)
        sa.Enum(name="workspace_role").drop(bind, checkfirst=True)