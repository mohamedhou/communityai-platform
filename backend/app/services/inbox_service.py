from __future__ import annotations

from datetime import UTC, datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.encryption import decrypt_token
from app.models.inbox_message import InboxMessage, InboxMessageType, InboxSentiment
from app.repositories.inbox_repository import InboxRepository
from app.schemas.ai import AIResponse
from app.schemas.inbox import (
    InboxListResponse,
    InboxMessageResponse,
    InboxSuggestReplyRequest,
    InboxUnreadCountResponse,
)
from app.services.ai_service import AIService
from app.social.models import SocialAccount, SocialAccountStatus
from app.social.providers.linkedin import LinkedInProvider
from app.social.providers.meta import MetaProvider


class InboxService:
    def __init__(
        self,
        repository: InboxRepository | None = None,
        ai_service: AIService | None = None,
    ):
        self.repository = repository or InboxRepository()
        self.ai_service = ai_service or AIService()

    def list_messages(
        self,
        db: Session,
        user_id: int,
        type: InboxMessageType | None = None,
        platform: str | None = None,
        sentiment: InboxSentiment | None = None,
        is_read: bool | None = None,
        is_resolved: bool | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> InboxListResponse:
        items, total = self.repository.list_messages(
            db=db,
            user_id=user_id,
            type=type,
            platform=platform,
            sentiment=sentiment,
            is_read=is_read,
            is_resolved=is_resolved,
            search=search,
            limit=limit,
            offset=offset,
        )
        unread_count = self.repository.count_unread(db=db, user_id=user_id)
        return InboxListResponse(
            items=[InboxMessageResponse.model_validate(item) for item in items],
            total=total,
            unread_count=unread_count,
        )

    def get_unread_count(self, db: Session, user_id: int) -> InboxUnreadCountResponse:
        unread_count = self.repository.count_unread(db=db, user_id=user_id)
        return InboxUnreadCountResponse(unread_count=unread_count)

    def get_message_by_id(self, db: Session, message_id: int, user_id: int) -> InboxMessage:
        message = self.repository.get_by_id(db=db, message_id=message_id, user_id=user_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interaction not found",
            )
        return message

    def mark_read(self, db: Session, message_id: int, user_id: int, is_read: bool = True) -> InboxMessage:
        message = self.get_message_by_id(db=db, message_id=message_id, user_id=user_id)
        return self.repository.update(db=db, db_obj=message, update_dict={"is_read": is_read})

    def mark_resolved(self, db: Session, message_id: int, user_id: int, is_resolved: bool = True) -> InboxMessage:
        message = self.get_message_by_id(db=db, message_id=message_id, user_id=user_id)
        return self.repository.update(db=db, db_obj=message, update_dict={"is_resolved": is_resolved})

    def suggest_reply(
        self,
        db: Session,
        message_id: int,
        user_id: int,
        req: InboxSuggestReplyRequest,
    ) -> AIResponse:
        message = self.get_message_by_id(db=db, message_id=message_id, user_id=user_id)
        platform_str = "social"
        if message.social_account:
            platform_str = message.social_account.platform or message.social_account.provider

        return self.ai_service.suggest_reply(
            content=message.content,
            interaction_type=message.type.value,
            platform=platform_str,
            sender_name=message.sender_name,
            sentiment=message.sentiment.value,
            tone=req.tone,
            instructions=req.instructions,
        )

    def send_reply(
        self,
        db: Session,
        message_id: int,
        user_id: int,
        content: str,
    ) -> InboxMessage:
        message = self.get_message_by_id(db=db, message_id=message_id, user_id=user_id)
        social_account = message.social_account or db.get(SocialAccount, message.social_account_id)
        if not social_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Social account associated with interaction is missing",
            )
        if social_account.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interaction not found",
            )

        # Decrypt social access token strictly backend-side
        access_token = decrypt_token(social_account.access_token_encrypted)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Social account token is missing or invalid",
            )

        provider_name = (social_account.provider or "").lower().strip()
        if provider_name == "meta":
            provider = MetaProvider()
        elif provider_name == "linkedin":
            provider = LinkedInProvider()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported social provider: {social_account.provider}",
            )

        # Dispatch reply via provider
        provider.send_reply(
            content=content,
            access_token=access_token,
            external_account_id=social_account.external_account_id,
            external_interaction_id=message.external_id,
            interaction_type=message.type.value,
        )

        # Update message state
        now = datetime.now(UTC)
        updated = self.repository.update(
            db=db,
            db_obj=message,
            update_dict={
                "replied_at": now,
                "is_resolved": True,
                "is_read": True,
            },
        )
        return updated

    def seed_mock(self, db: Session, user_id: int) -> list[InboxMessage]:
        settings = get_settings()
        if not settings.social_mock_mode:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mock mode is disabled",
            )

        # Find or create a mock social account for this user
        account = (
            db.query(SocialAccount)
            .filter(SocialAccount.user_id == user_id)
            .first()
        )
        if not account:
            from app.core.encryption import encrypt_token

            account = SocialAccount(
                user_id=user_id,
                platform="facebook",
                provider="meta",
                external_account_id="mock_fb_acc_123",
                account_name="CommunityAI Mock Page",
                account_username="communityai_page",
                profile_image_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe",
                access_token_encrypted=encrypt_token("mock-token"),
                status=SocialAccountStatus.CONNECTED,
            )
            db.add(account)
            db.commit()
            db.refresh(account)

        return self.repository.seed_mock_interactions(
            db=db,
            user_id=user_id,
            social_account_id=account.id,
        )
