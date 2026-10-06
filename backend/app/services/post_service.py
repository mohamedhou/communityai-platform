from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_token
from app.models.post import Post, PostApprovalStatus, PostStatus
from app.models.user import User
from app.models.workspace import MembershipStatus, WorkspaceActivity, WorkspaceMember, WorkspaceRole
from app.social.models import SocialAccount
from app.social.providers.linkedin import LinkedInProvider
from app.social.providers.meta import MetaProvider
from app.social.exceptions import SocialProviderError


class PostService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_transition(self, current_status: PostStatus, new_status: PostStatus) -> None:
        allowed_transitions = {
            PostStatus.DRAFT: {PostStatus.PUBLISHING, PostStatus.SCHEDULED, PostStatus.CANCELLED},
            PostStatus.SCHEDULED: {PostStatus.PUBLISHING, PostStatus.CANCELLED},
            PostStatus.PUBLISHING: {PostStatus.PUBLISHED, PostStatus.FAILED},
        }
        if current_status == new_status:
            return
        if current_status not in allowed_transitions or new_status not in allowed_transitions[current_status]:
            raise ValueError(f"Invalid status transition from {current_status} to {new_status}")

    def _log_activity(self, workspace_id: int, actor_id: int | None, event: str, details: str) -> None:
        self.db.add(WorkspaceActivity(workspace_id=workspace_id, actor_id=actor_id, event=event, details=details))
        self.db.commit()

    def create_post(
        self,
        *,
        user_id: int,
        social_account_id: int,
        content: str,
        media_url: str | None = None,
        workspace_id: int | None = None,
    ) -> Post:
        social_account = self.db.get(SocialAccount, social_account_id)
        if not social_account:
            raise ValueError("social_account_not_found")

        if workspace_id is None:
            workspace_id = social_account.workspace_id
        elif social_account.workspace_id != workspace_id:
            raise PermissionError("not_authorized")

        post = Post(
            workspace_id=workspace_id,
            user_id=user_id,
            social_account_id=social_account_id,
            content=content,
            media_url=media_url,
            status=PostStatus.DRAFT,
            approval_status=PostApprovalStatus.NOT_REQUIRED,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_post_by_id(
        self,
        workspace_id: int,
        post_id: int,
    ) -> Post:
        post = self.db.get(Post, post_id)
        if not post:
            raise ValueError("post_not_found")
        if post.workspace_id != workspace_id:
            raise PermissionError("not_authorized")
        return post

    def list_posts(
        self,
        workspace_id: int,
        status: PostStatus | None = None,
        approval_status: PostApprovalStatus | None = None,
    ) -> list[Post]:
        stmt = select(Post).where(Post.workspace_id == workspace_id)
        if status:
            stmt = stmt.where(Post.status == status)
        if approval_status:
            stmt = stmt.where(Post.approval_status == approval_status)
        stmt = stmt.order_by(Post.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def update_post(
        self,
        workspace_id: int,
        post_id: int,
        *,
        content: str | None = None,
        media_url: str | None = None,
        social_account_id: int | None = None,
    ) -> Post:
        post = self.get_post_by_id(workspace_id, post_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.SCHEDULED, PostStatus.FAILED):
            raise ValueError("Cannot edit a post that is publishing or published")

        material_change = False
        if social_account_id is not None and social_account_id != post.social_account_id:
            social_account = self.db.get(SocialAccount, social_account_id)
            if not social_account:
                raise ValueError("social_account_not_found")
            if social_account.workspace_id != workspace_id:
                raise PermissionError("not_authorized")
            post.social_account_id = social_account_id
            material_change = True

        if content is not None and content != post.content:
            post.content = content
            material_change = True
        if media_url is not None and media_url != post.media_url:
            post.media_url = media_url
            material_change = True

        # Invalidate approval if an APPROVED post is materially edited before publication
        if material_change and post.approval_status == PostApprovalStatus.APPROVED:
            post.approval_status = PostApprovalStatus.REJECTED
            post.rejection_reason = "Content modified after approval; resubmission required."
            post.reviewed_by = None
            post.reviewed_at = None
            if post.status == PostStatus.SCHEDULED:
                post.status = PostStatus.DRAFT
                post.scheduled_at = None

        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete_post(self, workspace_id: int, post_id: int) -> None:
        post = self.get_post_by_id(workspace_id, post_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.SCHEDULED, PostStatus.FAILED, PostStatus.CANCELLED):
            raise ValueError("Cannot delete a post that is publishing or published")
        self.db.delete(post)
        self.db.commit()

    def submit_for_review(self, workspace_id: int, post_id: int, user_id: int) -> Post:
        post = self.get_post_by_id(workspace_id, post_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.FAILED):
            raise ValueError("Only draft or failed posts can be submitted for review")
        if post.approval_status == PostApprovalStatus.PENDING:
            raise ValueError("Post is already pending review")
        if post.approval_status == PostApprovalStatus.APPROVED:
            raise ValueError("Post is already approved")

        was_rejected = post.approval_status == PostApprovalStatus.REJECTED
        post.approval_status = PostApprovalStatus.PENDING
        post.submitted_for_review_at = datetime.now(UTC)
        post.rejection_reason = None

        if post.status == PostStatus.FAILED:
            post.status = PostStatus.DRAFT
            post.error_message = None

        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        event = "POST_RESUBMITTED" if was_rejected else "POST_SUBMITTED_FOR_REVIEW"
        self._log_activity(workspace_id, user_id, event, f"Post #{post.id} submitted for review")

        # Notify workspace reviewers (OWNER and ADMIN)
        author = self.db.get(User, user_id)
        author_name = f"{author.first_name} {author.last_name}" if author else f"User #{user_id}"
        stmt = select(WorkspaceMember.user_id).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.role.in_([WorkspaceRole.OWNER, WorkspaceRole.ADMIN]),
            WorkspaceMember.status == MembershipStatus.ACTIVE,
        )
        reviewer_ids = [uid for uid in self.db.execute(stmt).scalars().all() if uid != user_id]
        if reviewer_ids:
            try:
                from app.services.notification_service import NotificationService

                notif_svc = NotificationService()
                if was_rejected:
                    notif_svc.notify_post_resubmitted(self.db, reviewer_ids, post.id, author_name)
                else:
                    notif_svc.notify_post_submitted_for_review(self.db, reviewer_ids, post.id, author_name)
            except Exception:
                pass

        return post

    def approve_post(
        self,
        workspace_id: int,
        post_id: int,
        reviewer_id: int,
        reviewer_role: WorkspaceRole,
    ) -> Post:
        if reviewer_role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            raise PermissionError("Only workspace owners and admins can approve posts")

        post = self.get_post_by_id(workspace_id, post_id)
        if post.approval_status != PostApprovalStatus.PENDING:
            raise ValueError("Only posts pending review can be approved")

        post.approval_status = PostApprovalStatus.APPROVED
        post.reviewed_by = reviewer_id
        post.reviewed_at = datetime.now(UTC)
        post.rejection_reason = None

        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        self._log_activity(workspace_id, reviewer_id, "POST_APPROVED", f"Post #{post.id} approved")

        reviewer = self.db.get(User, reviewer_id)
        reviewer_name = f"{reviewer.first_name} {reviewer.last_name}" if reviewer else "Reviewer"
        try:
            from app.services.notification_service import NotificationService

            NotificationService().notify_post_approved(self.db, post.user_id, post.id, reviewer_name)
        except Exception:
            pass

        return post

    def reject_post(
        self,
        workspace_id: int,
        post_id: int,
        reviewer_id: int,
        reviewer_role: WorkspaceRole,
        reason: str,
    ) -> Post:
        if reviewer_role not in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            raise PermissionError("Only workspace owners and admins can reject posts")

        clean_reason = (reason or "").strip()
        if not clean_reason:
            raise ValueError("Rejection reason is required")

        post = self.get_post_by_id(workspace_id, post_id)
        if post.approval_status != PostApprovalStatus.PENDING:
            raise ValueError("Only posts pending review can be rejected")

        post.approval_status = PostApprovalStatus.REJECTED
        post.reviewed_by = reviewer_id
        post.reviewed_at = datetime.now(UTC)
        post.rejection_reason = clean_reason

        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        self._log_activity(workspace_id, reviewer_id, "POST_REJECTED", f"Post #{post.id} rejected: {clean_reason}")

        reviewer = self.db.get(User, reviewer_id)
        reviewer_name = f"{reviewer.first_name} {reviewer.last_name}" if reviewer else "Reviewer"
        try:
            from app.services.notification_service import NotificationService

            NotificationService().notify_post_rejected(self.db, post.user_id, post.id, reviewer_name, clean_reason)
        except Exception:
            pass

        return post

    def list_review_queue(self, workspace_id: int) -> list[Post]:
        stmt = (
            select(Post)
            .where(Post.workspace_id == workspace_id, Post.approval_status == PostApprovalStatus.PENDING)
            .order_by(Post.submitted_for_review_at.desc().nulls_last(), Post.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_review_history(self, workspace_id: int) -> list[Post]:
        stmt = (
            select(Post)
            .where(
                Post.workspace_id == workspace_id,
                Post.approval_status.in_([PostApprovalStatus.APPROVED, PostApprovalStatus.REJECTED]),
            )
            .order_by(Post.reviewed_at.desc().nulls_last(), Post.updated_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def schedule_post(
        self,
        workspace_id: int | None = None,
        post_id: int | None = None,
        scheduled_at: datetime | None = None,
        actor_user_id: int | None = None,
        user_id: int | None = None,
        actor_role: WorkspaceRole | None = None,
    ) -> Post:
        if post_id is None:
            raise ValueError("post_not_found")
        if scheduled_at is None:
            raise ValueError("Scheduled time is required")
        if workspace_id is None:
            raw_post = self.db.get(Post, post_id)
            if not raw_post:
                raise ValueError("post_not_found")
            workspace_id = raw_post.workspace_id

        post = self.get_post_by_id(workspace_id, post_id)

        # Server-side publishing safety: check approval status and role policy
        if actor_role == WorkspaceRole.COMMUNITY_MANAGER:
            if post.approval_status != PostApprovalStatus.APPROVED:
                raise PermissionError("Community managers can only schedule approved posts")
        elif actor_role in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            if post.approval_status in (PostApprovalStatus.PENDING, PostApprovalStatus.REJECTED):
                raise ValueError(f"Post cannot be scheduled while approval status is {post.approval_status}")
        else:
            if post.approval_status in (PostApprovalStatus.PENDING, PostApprovalStatus.REJECTED):
                raise ValueError(f"Post cannot be scheduled while approval status is {post.approval_status}")

        self._validate_transition(post.status, PostStatus.SCHEDULED)

        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=UTC)

        if scheduled_at <= datetime.now(UTC):
            raise ValueError("Scheduled time must be in the future")

        post.status = PostStatus.SCHEDULED
        post.scheduled_at = scheduled_at
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        try:
            from app.services.notification_service import NotificationService

            notify_user_id = actor_user_id or user_id or post.user_id
            NotificationService().notify_post_scheduled(
                db=self.db,
                user_id=notify_user_id,
                post_id=post.id,
                scheduled_at=scheduled_at,
            )
        except Exception:
            pass

        return post

    def cancel_post(
        self,
        workspace_id: int | None = None,
        post_id: int | None = None,
        user_id: int | None = None,
    ) -> Post:
        if post_id is None:
            raise ValueError("post_not_found")
        if workspace_id is None:
            raw_post = self.db.get(Post, post_id)
            if not raw_post:
                raise ValueError("post_not_found")
            workspace_id = raw_post.workspace_id

        post = self.get_post_by_id(workspace_id, post_id)
        self._validate_transition(post.status, PostStatus.CANCELLED)

        post.status = PostStatus.CANCELLED
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def publish_post(
        self,
        workspace_id: int,
        post_id: int,
        actor_role: WorkspaceRole | None = None,
    ) -> Post:
        stmt = select(Post).where(Post.id == post_id).with_for_update()
        post = self.db.execute(stmt).scalar_one_or_none()

        if not post:
            raise ValueError("post_not_found")
        if post.workspace_id != workspace_id:
            raise PermissionError("not_authorized")

        # Community managers need explicit approval; owners/admins may publish drafts.
        if actor_role == WorkspaceRole.COMMUNITY_MANAGER and post.approval_status != PostApprovalStatus.APPROVED:
            raise PermissionError("Community managers can only publish approved posts")
        allowed_approval = (
            (PostApprovalStatus.APPROVED,)
            if actor_role == WorkspaceRole.COMMUNITY_MANAGER
            else (PostApprovalStatus.NOT_REQUIRED, PostApprovalStatus.APPROVED)
        )
        if post.approval_status not in allowed_approval:
            raise ValueError(f"Post cannot be published while approval status is {post.approval_status}")

        if post.status in (PostStatus.PUBLISHING, PostStatus.PUBLISHED):
            raise ValueError("Post is already publishing or published")

        self._validate_transition(post.status, PostStatus.PUBLISHING)

        social_account = self.db.get(SocialAccount, post.social_account_id)
        if not social_account:
            raise ValueError("social_account_not_found")
        if social_account.workspace_id != workspace_id:
            raise PermissionError("not_authorized")

        post.status = PostStatus.PUBLISHING
        post.error_message = None
        self.db.add(post)
        self.db.commit()

        try:
            if social_account.provider == "meta":
                provider = MetaProvider()
            elif social_account.provider == "linkedin":
                provider = LinkedInProvider()
            else:
                raise ValueError(f"Unsupported provider: {social_account.provider}")

            decrypted_access_token = decrypt_token(social_account.access_token_encrypted)
            external_post_id = provider.publish_post(
                content=post.content,
                access_token=decrypted_access_token,
                external_account_id=social_account.external_account_id,
                media_url=post.media_url,
            )

            post.status = PostStatus.PUBLISHED
            post.external_post_id = external_post_id
            post.published_at = datetime.now(UTC)
            post.error_message = None
            self.db.add(post)
            self.db.commit()
            self.db.refresh(post)

            try:
                from app.services.notification_service import NotificationService

                NotificationService().notify_post_published(
                    db=self.db,
                    user_id=post.user_id,
                    post_id=post.id,
                    platform=social_account.platform,
                )
            except Exception:
                pass

        except SocialProviderError as exc:
            post.status = PostStatus.FAILED
            post.error_message = str(exc)
            self.db.add(post)
            self.db.commit()
            self.db.refresh(post)

            try:
                from app.services.notification_service import NotificationService

                NotificationService().notify_post_failed(
                    db=self.db,
                    user_id=post.user_id,
                    post_id=post.id,
                    error_message=str(exc),
                    platform=social_account.platform,
                )
            except Exception:
                pass

        except Exception as exc:
            post.status = PostStatus.FAILED
            post.error_message = f"Unexpected error: {str(exc)}"
            self.db.add(post)
            self.db.commit()
            self.db.refresh(post)

            try:
                from app.services.notification_service import NotificationService

                NotificationService().notify_post_failed(
                    db=self.db,
                    user_id=post.user_id,
                    post_id=post.id,
                    error_message=f"Unexpected error: {str(exc)}",
                    platform=social_account.platform,
                )
            except Exception:
                pass

        return post
