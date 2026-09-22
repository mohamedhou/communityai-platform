# True Workspace & Team Collaboration

## Architecture Overview

CommunityAI implements multi-tenant team collaboration through genuine **Workspace Data Isolation**. The `Workspace` entity serves as the authoritative boundary for all agency assets and team activities.

### Core Tenancy Model
- **Workspaces (`workspaces`)**: Top-level agency container possessing assets, members, invitations, and audit logs.
- **Workspace Memberships (`workspace_members`)**: Maps users to workspaces with granular roles (`OWNER`, `ADMIN`, `COMMUNITY_MANAGER`, `CLIENT`) and membership status (`ACTIVE`, `INACTIVE`).
- **Workspace Invitations (`workspace_invitations`)**: Secure token-based invitation lifecycle with SHA-256 token hashing, 7-day expiration, and one-time acceptance.
- **Workspace Activity Log (`workspace_activities`)**: Tamper-evident audit trail recording invitation sends, acceptances, revocations, role changes, status updates, and member removals.

### Business Resources Scoped to Workspaces
All shared business resources now enforce direct workspace tenancy with foreign key relationships (`workspace_id` NOT NULL with `ON DELETE CASCADE`) and database indexes:
1. **`social_accounts`**: Connected social profiles (Facebook, Instagram, LinkedIn) belong directly to the workspace. When any team member creates or schedules content, the social account is available workspace-wide.
2. **`posts`**: Draft, scheduled, and published posts are workspace-scoped. Collaborators in the same workspace can review, edit, and publish posts. `user_id` is preserved for creator attribution.
3. **`inbox_messages`**: Inbound comments, direct messages, and mentions are ingested at the workspace level. Community managers collaborate on the shared inbox, mark status, and send replies.
4. **`analytics_snapshots`**: Follower growth, reach, impressions, and engagement metrics are aggregated strictly within the active workspace.
5. **`oauth_states`**: OAuth initiation stores `workspace_id` in the database, guaranteeing that the completed OAuth callback links the external social profile to the exact initiating workspace.

---

## Workspace Context Resolution

Workspaces are resolved on every authenticated request via a centralized dependency: `get_workspace_context`:
1. **Optional Header (`X-Workspace-ID`)**: If the client provides `X-Workspace-ID`, the dependency validates that the authenticated user has an active membership (`MembershipStatus.ACTIVE`) in that specific workspace. If the user is not an active member, the request is immediately rejected with `403 Forbidden`.
2. **Default Workspace Fallback**: If no header is supplied, the user's primary active workspace is resolved. For single-workspace agencies or existing users, a default workspace is automatically provisioned.
3. **Role Enforcement**:
   - `require_workspace_editor`: Ensures caller is `OWNER`, `ADMIN`, or `COMMUNITY_MANAGER` (blocks read-only `CLIENT` users with `403 Forbidden`).
   - `require_workspace_manager`: Ensures caller is `OWNER` or `ADMIN` for team management operations.

---

## Roles and Permissions Matrix

| Capability | OWNER | ADMIN | COMMUNITY MANAGER | CLIENT |
|:---|:---:|:---:|:---:|:---:|
| View Workspace Content & Analytics | Yes | Yes | Yes | Yes (Read-only) |
| Manage Social Accounts & OAuth | Yes | Yes | Yes | No |
| Create, Edit & Schedule Posts | Yes | Yes | Yes | No |
| Publish Posts & Reply to Inbox | Yes | Yes | Yes | No |
| Invite New Members | Yes | Yes | No | No |
| Change Member Roles | Yes | Yes (Non-owners) | No | No |
| Deactivate / Remove Members | Yes | Yes (Non-owners) | No | No |
| Delete / Modify Workspace Owner | No (Protected) | No | No | No |

---

## Invitation Security & Lifecycle

1. **Token Generation**: Generates 32 bytes of cryptographically random entropy via `secrets.token_urlsafe(32)`.
2. **Token Storage**: Raw tokens are never stored in the database. Only the SHA-256 digest (`hash_token(raw_token)`) is persisted.
3. **Token Expiration**: Invitations automatically expire after 7 days.
4. **Single-Use Acceptance**: Once accepted, `accepted_at` timestamp is written and the invitation cannot be reused.
5. **Identity Verification**: During acceptance, the authenticated user's email is strictly compared against the invited email. Mismatched emails are rejected with `403 Forbidden`.
6. **Public Preview**: Public endpoint `GET /api/v1/workspace/invitations/{token}` allows invited users to preview workspace details before logging in or registering.

---

## Workspace API Endpoints

All team and workspace management endpoints use the singular `/api/v1/workspace` route prefix (not plural `/api/v1/workspaces`):
- `GET /api/v1/workspace/members`: List active workspace members.
- `POST /api/v1/workspace/invitations`: Create and send workspace invitation.
- `GET /api/v1/workspace/invitations`: List pending workspace invitations.
- `POST /api/v1/workspace/invitations/{invitation_id}/revoke`: Revoke an open invitation.
- `PATCH /api/v1/workspace/members/{member_id}/role`: Update member role (`OWNER`, `ADMIN`, `COMMUNITY_MANAGER`, `CLIENT`).
- `PATCH /api/v1/workspace/members/{member_id}/status`: Update member status (`ACTIVE`, `INACTIVE`).
- `DELETE /api/v1/workspace/members/{member_id}`: Remove a member from the workspace.
- `GET /api/v1/workspace/invitations/{token}`: Publicly preview invitation details.
- `POST /api/v1/workspace/invitations/{token}/accept`: Authenticated acceptance of invitation.

---

## Database Migrations

The migration chain strictly follows a single linear history:
`0008_create_user_settings` -> `0009_create_workspaces` -> `0010_add_workspace_isolation (head)`

- **`0009_create_workspaces.py`** (revises `0008_create_user_settings`):
  - Creates `workspaces`, `workspace_members`, `workspace_invitations`, and `workspace_activities` tables.
  - Handles PostgreSQL/SQLite dialect-safe ENUM types for `workspace_role` and `membership_status` (`ACTIVE`, `INACTIVE`).
  - Extends `notification_type` with `WORKSPACE`.
  - Automatically provisions an initial primary workspace and assigns `OWNER` role for existing users.
- **`0010_add_workspace_isolation.py`** (revises `0009_create_workspaces`):
  - Adds `workspace_id` to `social_accounts`, `posts`, `inbox_messages`, `analytics_snapshots`, and `oauth_states`.
  - Backfills existing records safely from user workspaces.
  - Enforces `NOT NULL` constraint on business resources (`social_accounts`, `posts`, `inbox_messages`, `analytics_snapshots`).
  - Creates foreign keys to `workspaces.id` with `ON DELETE CASCADE`.
  - Creates indexes on `workspace_id` for optimal query performance.

---

## Verification & Testing

The implementation is verified by 126 automated backend tests:
- **MVP Functionality**: 113 tests covering authentication, RBAC, social accounts, post publishing, calendar, inbox, analytics, notifications, and reporting.
- **Team Management (`tests/test_workspace.py`)**: 7 tests covering member listing, invitation flows, duplicate rejections, role modifications, owner protection, and status toggles.
- **Data Isolation (`tests/test_workspace_isolation.py`)**: 6 tests verifying cross-workspace data siloing, unauthorized ID probing, same-workspace collaboration, header spoofing protection, and OAuth workspace binding.