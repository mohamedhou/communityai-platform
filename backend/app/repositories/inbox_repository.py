from __future__ import annotations

from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.inbox_message import InboxMessage, InboxMessageType, InboxSentiment
from app.schemas.inbox import InboxMessageCreate
from app.social.models import SocialAccount


class InboxRepository:
    def get_by_id(self, db: Session, message_id: int, user_id: int | None = None) -> InboxMessage | None:
        query = (
            select(InboxMessage)
            .options(joinedload(InboxMessage.social_account))
            .where(InboxMessage.id == message_id)
        )
        if user_id is not None:
            query = query.where(InboxMessage.user_id == user_id)
        return db.scalars(query).first()

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
    ) -> tuple[list[InboxMessage], int]:
        base_query = (
            select(InboxMessage)
            .options(joinedload(InboxMessage.social_account))
            .where(InboxMessage.user_id == user_id)
        )

        if platform:
            plat_clean = platform.strip().lower()
            base_query = base_query.join(SocialAccount, InboxMessage.social_account_id == SocialAccount.id).where(
                or_(
                    func.lower(SocialAccount.platform) == plat_clean,
                    func.lower(SocialAccount.provider) == plat_clean,
                )
            )

        if type:
            base_query = base_query.where(InboxMessage.type == type)

        if sentiment:
            base_query = base_query.where(InboxMessage.sentiment == sentiment)

        if is_read is not None:
            base_query = base_query.where(InboxMessage.is_read == is_read)

        if is_resolved is not None:
            base_query = base_query.where(InboxMessage.is_resolved == is_resolved)

        if search:
            search_pattern = f"%{search.strip()}%"
            base_query = base_query.where(
                or_(
                    InboxMessage.content.ilike(search_pattern),
                    InboxMessage.sender_name.ilike(search_pattern),
                )
            )

        # Count total matching query
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = db.scalar(count_stmt) or 0

        # Fetch paginated items ordered by created_at desc
        stmt = base_query.order_by(InboxMessage.created_at.desc()).offset(offset).limit(limit)
        items = list(db.scalars(stmt).unique().all())

        return items, total

    def count_unread(self, db: Session, user_id: int) -> int:
        stmt = select(func.count()).select_from(InboxMessage).where(
            InboxMessage.user_id == user_id,
            InboxMessage.is_read.is_(False),
        )
        return db.scalar(stmt) or 0

    def create(self, db: Session, message_in: InboxMessageCreate) -> InboxMessage:
        db_obj = InboxMessage(
            user_id=message_in.user_id,
            social_account_id=message_in.social_account_id,
            external_id=message_in.external_id,
            type=message_in.type,
            sender_name=message_in.sender_name,
            sender_external_id=message_in.sender_external_id,
            content=message_in.content,
            sentiment=message_in.sentiment,
            sentiment_score=message_in.sentiment_score,
            is_read=message_in.is_read,
            is_resolved=message_in.is_resolved,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: InboxMessage, update_dict: dict[str, Any]) -> InboxMessage:
        for key, value in update_dict.items():
            setattr(db_obj, key, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def seed_mock_interactions(
        self, db: Session, user_id: int, social_account_id: int
    ) -> list[InboxMessage]:
        mock_data = [
            InboxMessageCreate(
                user_id=user_id,
                social_account_id=social_account_id,
                external_id=f"mock_ext_neg_{user_id}_{social_account_id}_1",
                type=InboxMessageType.COMMENT,
                sender_name="Jean-Marc Martin",
                sender_external_id="user_fb_987",
                content="Votre nouvelle mise à jour a cassé mon export de données, c'est inadmissible !",
                sentiment=InboxSentiment.NEGATIVE,
                sentiment_score=-0.85,
                is_read=False,
                is_resolved=False,
            ),
            InboxMessageCreate(
                user_id=user_id,
                social_account_id=social_account_id,
                external_id=f"mock_ext_pos_{user_id}_{social_account_id}_2",
                type=InboxMessageType.COMMENT,
                sender_name="Sophie Laurent",
                sender_external_id="user_li_456",
                content="Superbe plateforme, le gain de temps pour mon équipe de CM est incroyable 🚀 Bravo !",
                sentiment=InboxSentiment.POSITIVE,
                sentiment_score=0.92,
                is_read=False,
                is_resolved=False,
            ),
            InboxMessageCreate(
                user_id=user_id,
                social_account_id=social_account_id,
                external_id=f"mock_ext_neu_{user_id}_{social_account_id}_3",
                type=InboxMessageType.COMMENT,
                sender_name="Alexandre Dupont",
                sender_external_id="user_ig_321",
                content="Bonjour, prévoyez-vous une intégration avec Pinterest ou TikTok prochainement ?",
                sentiment=InboxSentiment.NEUTRAL,
                sentiment_score=0.05,
                is_read=True,
                is_resolved=False,
            ),
            InboxMessageCreate(
                user_id=user_id,
                social_account_id=social_account_id,
                external_id=f"mock_ext_msg_{user_id}_{social_account_id}_4",
                type=InboxMessageType.MESSAGE,
                sender_name="Camille Bernard",
                sender_external_id="user_li_789",
                content="Bonjour l'équipe CommunityAI, j'aimerais avoir des informations sur vos tarifs entreprises et la gestion multi-marques.",
                sentiment=InboxSentiment.NEUTRAL,
                sentiment_score=0.12,
                is_read=False,
                is_resolved=False,
            ),
            InboxMessageCreate(
                user_id=user_id,
                social_account_id=social_account_id,
                external_id=f"mock_ext_men_{user_id}_{social_account_id}_5",
                type=InboxMessageType.MENTION,
                sender_name="TechDaily Review",
                sender_external_id="user_meta_555",
                content="@CommunityAI est sans doute le meilleur outil d'automatisation et de gestion sociale que nous ayons testé en 2026. À essayer absolument !",
                sentiment=InboxSentiment.POSITIVE,
                sentiment_score=0.88,
                is_read=False,
                is_resolved=False,
            ),
        ]

        created = []
        for item in mock_data:
            created.append(self.create(db, item))
        return created
