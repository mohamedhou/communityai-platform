from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_token
from app.models.post import Post, PostStatus
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

    def list_posts(self, workspace_id: int, status: PostStatus | None = None) -> list[Post]:
        stmt = select(Post).where(Post.workspace_id == workspace_id)
        if status:
            stmt = stmt.where(Post.status == status)
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

        if social_account_id is not None:
            social_account = self.db.get(SocialAccount, social_account_id)
            if not social_account:
                raise ValueError("social_account_not_found")
            if social_account.workspace_id != workspace_id:
                raise PermissionError("not_authorized")
            post.social_account_id = social_account_id

        if content is not None:
            post.content = content
        if media_url is not None:
            post.media_url = media_url

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

    def schedule_post(
        self,
        workspace_id: int | None = None,
        post_id: int | None = None,
        scheduled_at: datetime | None = None,
        actor_user_id: int | None = None,
        user_id: int | None = None,
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

    def publish_post(self, workspace_id: int, post_id: int) -> Post:
        stmt = select(Post).where(Post.id == post_id).with_for_update()
        post = self.db.execute(stmt).scalar_one_or_none()

        if not post:
            raise ValueError("post_not_found")
        if post.workspace_id != workspace_id:
            raise PermissionError("not_authorized")

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
