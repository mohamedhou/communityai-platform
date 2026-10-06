# Content Approval & Review Workflow

## Architecture & Lifecycle Overview

CommunityAI implements an enterprise-grade **Content Approval & Review Workflow** designed for agencies and marketing teams. The system enables Community Managers to draft content and submit it for editorial review, while Workspace Owners and Admins review, approve, or reject submissions with mandatory feedback.

### Decoupled Status Lifecycles

The approval workflow strictly decouples the editorial review process from the post publication lifecycle:

1. **Publication Lifecycle (`PostStatus`)**:
   - `DRAFT`: Preliminary editable post.
   - `SCHEDULED`: Approved and set for automated release at `scheduled_at`.
   - `PUBLISHING`: In transit via background worker.
   - `PUBLISHED`: Live on external social networks (Meta, LinkedIn).
   - `FAILED`: Execution or API failure with error log.
   - `CANCELLED`: User or manager cancelled release.

2. **Approval Lifecycle (`PostApprovalStatus`)**:
   - `NOT_REQUIRED`: Default status for existing or unsubmitted drafts.
   - `PENDING`: Submitted to the workspace review queue, awaiting reviewer evaluation.
   - `APPROVED`: Validated by an Owner or Admin; eligible for immediate publication or scheduling.
   - `REJECTED`: Rejected by a reviewer with mandatory feedback reason, or automatically reset due to post-approval content modification.

---

## Roles and Permissions Matrix

| Capability | OWNER | ADMIN | COMMUNITY_MANAGER | CLIENT |
|:---|:---:|:---:|:---:|:---:|
| Create / Edit Draft Posts | Yes | Yes | Yes | No |
| Submit Post for Review | Yes | Yes | Yes | No |
| View Review Queue & History | Yes | Yes | Yes (Read-only) | No |
| Approve Posts | **Yes** | **Yes** | **No** (403 Forbidden) | **No** (403 Forbidden) |
| Reject Posts (with Reason) | **Yes** | **Yes** | **No** (403 Forbidden) | **No** (403 Forbidden) |
| Schedule / Publish Approved Posts | Yes | Yes | Yes | No |
| Schedule / Publish Unapproved Posts | **Blocked** | **Blocked** | **Blocked** | **Blocked** |

> [!IMPORTANT]
> **Strict Server-Side Protection**: Only workspace `OWNER` and `ADMIN` roles are authorized to invoke `/approve` and `/reject`. `COMMUNITY_MANAGER` can draft, revise, and submit content for review, but cannot approve or reject posts. `CLIENT` has read-only access to published/scheduled content and cannot participate in editorial submissions.

---

## Server-Side Publishing Safety & Guarantees

Content safety is enforced strictly at the database and service layer, preventing any client-side or direct API bypass:

1. **Immediate Publishing Guard**:
   - Any invocation of `POST /api/v1/posts/{post_id}/publish` checks the post's `approval_status`.
   - If `approval_status` is `PENDING` or `REJECTED`, the request is immediately rejected with `400 Bad Request`:
     - *"Cannot publish post pending approval. Must be approved first."*
     - *"Cannot publish rejected post. Must be revised and approved first."*

2. **Scheduling Guard**:
   - Any invocation of `POST /api/v1/posts/{post_id}/schedule` validates `approval_status`.
   - If `approval_status` is `PENDING` or `REJECTED`, the request is rejected with `400 Bad Request`.

3. **Material Edit Invalidation**:
   - When an already `APPROVED` post is modified prior to publication (content, media, or social account change), the service layer automatically invalidates the approval:
     - `approval_status` resets to `REJECTED`.
     - `rejection_reason` is set to: *"Content modified after approval; resubmission required."*
     - A notification and audit log are dispatched, ensuring no unapproved content can be sneakily modified and published.

4. **Multi-Tenant Workspace Scoping**:
   - All review endpoints operate strictly within the caller's active workspace (`context.workspace_id`).
   - Cross-workspace review attempts are rejected with `404 Not Found` or `403 Forbidden`.

---

## Workspace Activity Audit Log & Notifications

Every approval lifecycle transition triggers real-time in-app notifications and persistent application audit events in `workspace_activities`. `WorkspaceActivity` is append-only at the application level, but it is not cryptographically tamper-evident: it does not use hash chaining or digital signatures:

| Transition | Activity Event Action | Recipient Notification | Target Users |
|:---|:---|:---|:---|
| **Submit for Review** | `POST_SUBMITTED_FOR_REVIEW` | `post_submitted_for_review` | Workspace Owners & Admins |
| **Resubmit for Review** | `POST_RESUBMITTED` | `post_resubmitted` | Workspace Owners & Admins |
| **Approve Post** | `POST_APPROVED` | `post_approved` | Original Author (`user_id`) |
| **Reject Post** | `POST_REJECTED` | `post_rejected` | Original Author (`user_id`) with feedback |

---

## API Endpoints

### Review Queue & Editorial Operations

All routes require authentication (`Bearer <token>`) and an active workspace membership context (via `X-Workspace-ID` or primary workspace).

- **`GET /api/v1/posts/review/queue`**
  - Returns all posts currently in `PENDING` approval status for the active workspace.
  - Ordered by `submitted_for_review_at ASC`.

- **`GET /api/v1/posts/review/history`**
  - Returns the latest 50 posts reviewed (`APPROVED` or `REJECTED`) in the workspace.
  - Ordered by `reviewed_at DESC`.

- **`POST /api/v1/posts/{post_id}/submit-review`**
  - Submits a `DRAFT` or `FAILED` post for review.
  - Transition: sets `approval_status = PENDING` and updates `submitted_for_review_at`.
  - Permissions: `OWNER`, `ADMIN`, `COMMUNITY_MANAGER`.

- **`POST /api/v1/posts/{post_id}/approve`**
  - Approves a pending publication.
  - Transition: sets `approval_status = APPROVED`, records `reviewed_by` and `reviewed_at`.
  - Permissions: `OWNER`, `ADMIN` only.

- **`POST /api/v1/posts/{post_id}/reject`**
  - Rejects a pending publication.
  - Request body: `{"reason": "Feedback string (1-1000 characters)"}`.
  - Transition: sets `approval_status = REJECTED`, saves `rejection_reason`, records `reviewed_by` and `reviewed_at`.
  - Permissions: `OWNER`, `ADMIN` only.

- **`GET /api/v1/posts?approval_status={status}`**
  - Added query filter parameter `approval_status` to existing list posts endpoint.

---

## Database Schema & Migration

### Migration `0011_content_approval_workflow`
- Revision chain: `0010_add_workspace_isolation` → `0011_content_approval_workflow` (current `head`).
- Added PostgreSQL ENUM `postapprovalstatus`: `('NOT_REQUIRED', 'PENDING', 'APPROVED', 'REJECTED')`.
- Added columns to `posts` table:
  - `approval_status` (ENUM `postapprovalstatus`, default `'NOT_REQUIRED'`, NOT NULL)
  - `reviewed_by` (`INTEGER`, nullable, FK to `users.id` with `ON DELETE SET NULL`)
  - `reviewed_at` (`TIMESTAMP WITH TIME ZONE`, nullable)
  - `rejection_reason` (`VARCHAR(1000)`, nullable)
  - `submitted_for_review_at` (`TIMESTAMP WITH TIME ZONE`, nullable)
- Added indexes:
  - `ix_posts_approval_status` on `posts(approval_status)`
  - `ix_posts_submitted_for_review_at` on `posts(submitted_for_review_at)`
- Implements dialect-safe ENUM handling (`checkfirst=True`, `create_type=False` on column addition).

---

## Frontend Integration

1. **Review Queue Page (`/posts/review`)**:
   - Tabbed view: "Pending Review" (with dynamic count badge) and "Review History".
   - Approve action with loading states.
   - Reject modal dialog requiring detailed feedback.
   - Role notice alerting Community Managers and Clients that approval permissions belong to Owners and Admins.

2. **Publications Page (`/posts`)**:
   - Status chips showing both publication status and approval status (`⏳ In Review`, `✓ Approved`, `✕ Rejected`).
   - Revision banner highlighting reviewer rejection reasons directly on cards.
   - Quick "Submit for Review" button on unsubmitted/rejected drafts.
   - Disabled "Publish Now" button with informational tooltip when content approval is required.
   - Header navigation to `/posts/review` with pending counter.

3. **Publication Composer (`/posts/new`, `/posts/{id}/edit`)**:
   - Rejection feedback banner displaying the exact feedback note provided by the reviewer.
   - Approval invalidation notice alerting users that modifying approved posts requires re-approval.
   - "Save & Submit for Review" button streamlining the CM publishing workflow.

4. **Editorial Calendar (`/calendar`)**:
   - Approval status icons on event cards (`⏳`, `✓`, `✕`).
   - Drag-and-drop reschedule restriction: unapproved posts cannot be dragged onto new dates.
