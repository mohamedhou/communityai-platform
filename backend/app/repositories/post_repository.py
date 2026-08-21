from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.post import Post, PostStatus


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, post_id: int) -> Post | None:
        return self.db.get(Post, post_id)

    def list_by_user(self, user_id: int, status: PostStatus | None = None) -> list[Post]:
        stmt = select(Post).where(Post.user_id == user_id)
        if status:
            stmt = stmt.where(Post.status == status)
        stmt = stmt.order_by(Post.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        *,
        user_id: int,
        social_account_id: int,
        content: str,
        media_url: str | None = None,
        status: PostStatus = PostStatus.DRAFT,
    ) -> Post:
        post = Post(
            user_id=user_id,
            social_account_id=social_account_id,
            content=content,
            media_url=media_url,
            status=status,
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def update(self, post: Post, **kwargs) -> Post:
        for key, value in kwargs.items():
            if hasattr(post, key):
                setattr(post, key, value)
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete(self, post: Post) -> None:
        self.db.delete(post)
        self.db.commit()
