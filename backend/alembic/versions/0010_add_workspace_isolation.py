"""add workspace isolation to business resources

Revision ID: 0010_add_workspace_isolation
Revises: 0009_create_workspaces
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0010_add_workspace_isolation"
down_revision = "0009_create_workspaces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add workspace_id columns as nullable initially
    op.add_column("social_accounts", sa.Column("workspace_id", sa.Integer(), nullable=True))
    op.add_column("posts", sa.Column("workspace_id", sa.Integer(), nullable=True))
    op.add_column("inbox_messages", sa.Column("workspace_id", sa.Integer(), nullable=True))
    op.add_column("analytics_snapshots", sa.Column("workspace_id", sa.Integer(), nullable=True))
    op.add_column("oauth_states", sa.Column("workspace_id", sa.Integer(), nullable=True))

    # 2. Backfill existing records safely
    # 2a. Social accounts from user's primary/owned workspace
    op.execute(
        "UPDATE social_accounts SET workspace_id = ("
        "  SELECT w.id FROM workspaces w WHERE w.owner_id = social_accounts.user_id LIMIT 1"
        ") WHERE workspace_id IS NULL"
    )

    # 2b. Posts from social_accounts, fallback to user's workspace
    op.execute(
        "UPDATE posts SET workspace_id = ("
        "  SELECT sa.workspace_id FROM social_accounts sa WHERE sa.id = posts.social_account_id LIMIT 1"
        ") WHERE workspace_id IS NULL"
    )
    op.execute(
        "UPDATE posts SET workspace_id = ("
        "  SELECT w.id FROM workspaces w WHERE w.owner_id = posts.user_id LIMIT 1"
        ") WHERE workspace_id IS NULL"
    )

    # 2c. Inbox messages from social_accounts, fallback to user's workspace
    op.execute(
        "UPDATE inbox_messages SET workspace_id = ("
        "  SELECT sa.workspace_id FROM social_accounts sa WHERE sa.id = inbox_messages.social_account_id LIMIT 1"
        ") WHERE workspace_id IS NULL"
    )
    op.execute(
        "UPDATE inbox_messages SET workspace_id = ("
        "  SELECT w.id FROM workspaces w WHERE w.owner_id = inbox_messages.user_id LIMIT 1"
        ") WHERE workspace_id IS NULL"
    )

    # 2d. Analytics snapshots from social_accounts, fallback to user's workspace
    op.execute(
        "UPDATE analytics_snapshots SET workspace_id = ("
        "  SELECT sa.workspace_id FROM social_accounts sa WHERE sa.id = analytics_snapshots.social_account_id LIMIT 1"
        ") WHERE workspace_id IS NULL"
    )
    op.execute(
        "UPDATE analytics_snapshots SET workspace_id = ("
        "  SELECT w.id FROM workspaces w WHERE w.owner_id = analytics_snapshots.user_id LIMIT 1"
        ") WHERE workspace_id IS NULL"
    )

    # 2e. OAuth states from user's workspace
    op.execute(
        "UPDATE oauth_states SET workspace_id = ("
        "  SELECT w.id FROM workspaces w WHERE w.owner_id = oauth_states.user_id LIMIT 1"
        ") WHERE workspace_id IS NULL"
    )

    # 3. Enforce NOT NULL for business resources
    op.alter_column("social_accounts", "workspace_id", nullable=False)
    op.alter_column("posts", "workspace_id", nullable=False)
    op.alter_column("inbox_messages", "workspace_id", nullable=False)
    op.alter_column("analytics_snapshots", "workspace_id", nullable=False)

    # 4. Foreign keys and indexes
    op.create_foreign_key("fk_social_accounts_workspace_id", "social_accounts", "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_posts_workspace_id", "posts", "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_inbox_messages_workspace_id", "inbox_messages", "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_analytics_snapshots_workspace_id", "analytics_snapshots", "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_oauth_states_workspace_id", "oauth_states", "workspaces", ["workspace_id"], ["id"], ondelete="CASCADE")

    op.create_index("ix_social_accounts_workspace_id", "social_accounts", ["workspace_id"])
    op.create_index("ix_posts_workspace_id", "posts", ["workspace_id"])
    op.create_index("ix_inbox_messages_workspace_id", "inbox_messages", ["workspace_id"])
    op.create_index("ix_analytics_snapshots_workspace_id", "analytics_snapshots", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_analytics_snapshots_workspace_id", table_name="analytics_snapshots")
    op.drop_index("ix_inbox_messages_workspace_id", table_name="inbox_messages")
    op.drop_index("ix_posts_workspace_id", table_name="posts")
    op.drop_index("ix_social_accounts_workspace_id", table_name="social_accounts")

    op.drop_constraint("fk_oauth_states_workspace_id", "oauth_states", type_="foreignkey")
    op.drop_constraint("fk_analytics_snapshots_workspace_id", "analytics_snapshots", type_="foreignkey")
    op.drop_constraint("fk_inbox_messages_workspace_id", "inbox_messages", type_="foreignkey")
    op.drop_constraint("fk_posts_workspace_id", "posts", type_="foreignkey")
    op.drop_constraint("fk_social_accounts_workspace_id", "social_accounts", type_="foreignkey")

    op.drop_column("oauth_states", "workspace_id")
    op.drop_column("analytics_snapshots", "workspace_id")
    op.drop_column("inbox_messages", "workspace_id")
    op.drop_column("posts", "workspace_id")
    op.drop_column("social_accounts", "workspace_id")
