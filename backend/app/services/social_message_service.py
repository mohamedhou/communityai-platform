from __future__ import annotations

import logging
from datetime import UTC, datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.encryption import decrypt_token
from app.models.inbox_message import InboxMessage
from app.social.models import SocialAccount
from app.social.providers.linkedin import LinkedInProvider
from app.social.providers.meta import MetaProvider

logger = logging.getLogger(__name__)


class SocialMessageService:
    """
    Handles dispatching replies to official social platform APIs:
    - Meta (Facebook Page comments, Instagram comments)
    - LinkedIn (Post comments)
    Enforces security, token decryption, error handling, and platform capability checks.
    """

    def send_social_reply(
        self,
        db: Session,
        workspace_id: int,
        message: InboxMessage,
        content: str,
    ) -> str:
        """
        Dispatches reply to external platform.
        Returns external reply ID.
        """
        social_account = message.social_account or db.get(SocialAccount, message.social_account_id)
        if not social_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Compte social associé à l'interaction introuvable.",
            )

        if social_account.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé au compte social.",
            )

        # Check platform capability
        provider_name = (social_account.provider or "").lower().strip()
        interaction_type = message.type.value if hasattr(message.type, "value") else str(message.type)

        if provider_name == "linkedin" and interaction_type == "MESSAGE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "L'API officielle LinkedIn Community Management ne permet pas la réponse directe "
                    "aux messages privés sans accès partenaire Enterprise InMail. Veuillez répondre depuis LinkedIn."
                ),
            )

        # Decrypt token safely on backend
        access_token = decrypt_token(social_account.access_token_encrypted)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jeton d'accès du compte social manquant ou invalide. Veuillez reconnecter le compte.",
            )

        if provider_name == "meta":
            provider = MetaProvider()
        elif provider_name == "linkedin":
            provider = LinkedInProvider()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fournisseur social non supporté : {social_account.provider}",
            )

        try:
            external_reply_id = provider.send_reply(
                content=content,
                access_token=access_token,
                external_account_id=social_account.external_account_id,
                external_interaction_id=message.external_id,
                interaction_type=interaction_type,
            )
            return external_reply_id

        except Exception as exc:
            logger.error(
                "SocialMessageService: External API error replying to message %s via %s: %s",
                message.id,
                provider_name,
                exc,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Échec de l'envoi sur {provider_name.capitalize()} : {str(exc)}",
            ) from exc
