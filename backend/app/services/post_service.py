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
    ) -> Post:
        # Check ownership of social account
        social_account = self.db.get(SocialAccount, social_account_id)
        if not social_account:
            raise ValueError("social_account_not_found")
        if social_account.user_id != user_id:
            raise PermissionError("not_authorized")

        post = Post(
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

    def get_post_by_id(self, user_id: int, post_id: int) -> Post:
        post = self.db.get(Post, post_id)
        if not post:
            raise ValueError("post_not_found")
        if post.user_id != user_id:
            raise PermissionError("not_authorized")
        return post

    def list_posts(self, user_id: int, status: PostStatus | None = None) -> list[Post]:
        stmt = select(Post).where(Post.user_id == user_id)
        if status:
            stmt = stmt.where(Post.status == status)
        stmt = stmt.order_by(Post.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def update_post(
        self,
        user_id: int,
        post_id: int,
        *,
        content: str | None = None,
        media_url: str | None = None,
        social_account_id: int | None = None,
    ) -> Post:
        post = self.get_post_by_id(user_id, post_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.SCHEDULED, PostStatus.FAILED):
            raise ValueError("Cannot edit a post that is publishing or published")

        if social_account_id is not None:
            social_account = self.db.get(SocialAccount, social_account_id)
            if not social_account:
                raise ValueError("social_account_not_found")
            if social_account.user_id != user_id:
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

    def delete_post(self, user_id: int, post_id: int) -> None:
        post = self.get_post_by_id(user_id, post_id)
        if post.status not in (PostStatus.DRAFT, PostStatus.SCHEDULED, PostStatus.FAILED, PostStatus.CANCELLED):
            raise ValueError("Cannot delete a post that is publishing or published")
        self.db.delete(post)
        self.db.commit()

    def schedule_post(self, user_id: int, post_id: int, scheduled_at: datetime) -> Post:
        post = self.get_post_by_id(user_id, post_id)
        self._validate_transition(post.status, PostStatus.SCHEDULED)

        # Check if scheduled time is in the future
        if scheduled_at <= datetime.now(UTC):
            raise ValueError("Scheduled time must be in the future")

        post.status = PostStatus.SCHEDULED
        post.scheduled_at = scheduled_at
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def cancel_post(self, user_id: int, post_id: int) -> Post:
        post = self.get_post_by_id(user_id, post_id)
        self._validate_transition(post.status, PostStatus.CANCELLED)

        post.status = PostStatus.CANCELLED
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def publish_post(self, user_id: int, post_id: int) -> Post:
        # Use SELECT FOR UPDATE to handle concurrent requests transactionally
        stmt = select(Post).where(Post.id == post_id).with_for_update()
        post = self.db.execute(stmt).scalar_one_or_none()

        if not post:
            raise ValueError("post_not_found")
        if post.user_id != user_id:
            raise PermissionError("not_authorized")

        # Double-publish protection
        if post.status in (PostStatus.PUBLISHING, PostStatus.PUBLISHED):
            raise ValueError("Post is already publishing or published")

        # Check state transitions
        self._validate_transition(post.status, PostStatus.PUBLISHING)

        # Retrieve and check social account ownership
        social_account = self.db.get(SocialAccount, post.social_account_id)
        if not social_account:
            raise ValueError("social_account_not_found")
        if social_account.user_id != user_id:
            raise PermissionError("not_authorized")

        # Mark as PUBLISHING and commit immediately to unlock for other connections
        post.status = PostStatus.PUBLISHING
        post.error_message = None
        self.db.add(post)
        self.db.commit()

        # Instantiate provider
        provider_name = social_account.provider.lower().strip()
        try:
            # Decrypt access token backend-only
            access_token = decrypt_token(social_account.access_token_encrypted)
            if not access_token:
                raise ValueError("No access token configured for connected social account")

            if provider_name == "meta":
                provider = MetaProvider()
            elif provider_name == "linkedin":
                provider = LinkedInProvider()
            else:
                raise ValueError(f"Unknown social provider: {social_account.provider}")

            # Call provider
            external_post_id = provider.publish_post(
                content=post.content,
                access_token=access_token,
                external_account_id=social_account.external_account_id,
                media_url=post.media_url,
            )

            # Update DB with success
            post.status = PostStatus.PUBLISHED
            post.external_post_id = external_post_id
            post.published_at = datetime.now(UTC)
            self.db.add(post)
            self.db.commit()
        except Exception as exc:
            # Update DB with failure
            post.status = PostStatus.FAILED
            post.error_message = str(exc)
            self.db.add(post)
            self.db.commit()

        self.db.refresh(post)
        return post

    def publish_scheduled_posts(self) -> None:
        """Fetch all posts scheduled for now or in the past, and publish them."""
        now = datetime.now(UTC)
        stmt = select(Post).where(Post.status == PostStatus.SCHEDULED, Post.scheduled_at <= now)
        scheduled_posts = self.db.execute(stmt).scalars().all()

        for post in scheduled_posts:
            try:
                self.publish_post(post.user_id, post.id)
            except Exception:
                # Log or handle exceptions quietly to continue publishing others
                pass
