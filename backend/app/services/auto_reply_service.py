from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ai_community_manager import (
    AICMMode,
    AICMSettings,
    AIReplyDraft,
    AIReplyDraftStatus,
    AICMAuditLog,
)
from app.models.inbox_message import InboxMessage
from app.schemas.ai_community_manager import (
    AIAnalysisResult,
    AIReplyResult,
    IntentType,
    SentimentType,
)
from app.services.ai_analysis_service import AIAnalysisService
from app.services.ai_reply_service import AIReplyService
from app.services.social_message_service import SocialMessageService

logger = logging.getLogger(__name__)


class AutoReplyService:
    """
    Orchestrates the 3 reply modes (MANUAL, APPROVAL_REQUIRED, AUTOMATIC)
    with strict safety blocklists, approval workflows, and audit trails.
    """

    def __init__(
        self,
        analysis_service: AIAnalysisService | None = None,
        reply_service: AIReplyService | None = None,
        social_service: SocialMessageService | None = None,
    ):
        self.analysis_service = analysis_service or AIAnalysisService()
        self.reply_service = reply_service or AIReplyService()
        self.social_service = social_service or SocialMessageService()

    def get_or_create_settings(self, db: Session, workspace_id: int) -> AICMSettings:
        """Get or initialize workspace automation settings."""
        settings = (
            db.query(AICMSettings)
            .filter(AICMSettings.workspace_id == workspace_id)
            .first()
        )
        if not settings:
            settings = AICMSettings(
                workspace_id=workspace_id,
                mode=AICMMode.APPROVAL_REQUIRED,
                enabled_platforms=["facebook", "instagram", "linkedin"],
                allowed_languages=["fr", "en"],
                min_confidence_score=0.85,
                auto_reply_intents=["compliment", "question", "support_request"],
                blocked_intents=["complaint", "refund", "threat", "legal", "payment_issue", "spam"],
                working_hours_only=False,
                temperature=0.3,
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    def process_incoming_interaction(
        self,
        db: Session,
        workspace_id: int,
        message: InboxMessage,
    ) -> AIReplyDraft | None:
        """
        Executes complete pipeline for an incoming message:
        1. Analyzes message (sentiment, intent, urgency, risk, requires_human)
        2. Persists analysis on InboxMessage
        3. Generates grounded reply suggestion
        4. Evaluates whether automatic send is authorized under strict safety rules
        5. Creates AIReplyDraft and audit log
        """
        # 1. Structured Analysis
        platform_name = "social"
        if message.social_account:
            platform_name = message.social_account.platform or message.social_account.provider or "social"

        analysis: AIAnalysisResult = self.analysis_service.analyze_message(
            content=message.content,
            sender_name=message.sender_name,
            platform=platform_name,
        )

        # Update message with enriched analysis
        message.intent = analysis.intent.value if hasattr(analysis.intent, "value") else str(analysis.intent)
        message.urgency = analysis.urgency.value if hasattr(analysis.urgency, "value") else str(analysis.urgency)
        message.topic = analysis.topic
        message.language = analysis.language
        message.ai_analysis = analysis.model_dump()
        db.commit()
        db.refresh(message)

        # Audit analysis
        db.add(AICMAuditLog(
            workspace_id=workspace_id,
            inbox_message_id=message.id,
            user_id=None,
            action="ANALYZE",
            details={
                "intent": message.intent,
                "urgency": message.urgency,
                "sentiment": message.sentiment.value if message.sentiment else "UNKNOWN",
                "requires_human": analysis.requires_human,
                "confidence": analysis.confidence,
            },
        ))
        db.commit()

        # 2. Generate grounded reply draft
        reply_res: AIReplyResult = self.reply_service.generate_reply(
            db=db,
            workspace_id=workspace_id,
            incoming_message=message.content,
            sender_name=message.sender_name,
            sender_external_id=message.sender_external_id,
            platform=platform_name,
        )

        # 3. Create Draft record
        idempotency_str = f"{workspace_id}:{message.id}:{reply_res.reply_text[:50]}"
        idempotency_key = hashlib.sha256(idempotency_str.encode()).hexdigest()

        # Check existing draft to prevent duplicates
        existing_draft = (
            db.query(AIReplyDraft)
            .filter(AIReplyDraft.idempotency_key == idempotency_key)
            .first()
        )
        if existing_draft:
            return existing_draft

        draft = AIReplyDraft(
            workspace_id=workspace_id,
            inbox_message_id=message.id,
            reply_text=reply_res.reply_text,
            original_reply_text=reply_res.reply_text,
            confidence_score=reply_res.confidence,
            sources_used=reply_res.sources_used,
            status=AIReplyDraftStatus.SUGGESTED,
            requires_human=analysis.requires_human or reply_res.requires_human,
            escalation_reason=reply_res.escalation_reason or (analysis.reason if analysis.requires_human else None),
            created_by_ai=True,
            idempotency_key=idempotency_key,
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        # 4. Check workspace mode & safety conditions for Auto-Send
        settings = self.get_or_create_settings(db, workspace_id)

        # Mode evaluation
        if settings.mode == AICMMode.AUTOMATIC:
            can_auto_send, refusal_reason = self._evaluate_auto_send_safety(
                settings=settings,
                analysis=analysis,
                reply_result=reply_res,
                platform=platform_name,
            )

            if can_auto_send:
                logger.info(
                    "AutoReplyService: Message %s qualifies for AUTOMATIC dispatch.",
                    message.id,
                )
                self._dispatch_draft(db, draft, message, is_automatic=True)
            else:
                logger.info(
                    "AutoReplyService: Message %s blocked from auto-send: %s",
                    message.id,
                    refusal_reason,
                )
                db.add(AICMAuditLog(
                    workspace_id=workspace_id,
                    inbox_message_id=message.id,
                    user_id=None,
                    action="BLOCKED_AUTO_SEND",
                    details={"reason": refusal_reason},
                ))
                db.commit()
        else:
            db.add(AICMAuditLog(
                workspace_id=workspace_id,
                inbox_message_id=message.id,
                user_id=None,
                action="DRAFT_CREATED",
                details={
                    "mode": settings.mode.value,
                    "confidence": reply_res.confidence,
                    "requires_human": draft.requires_human,
                },
            ))
            db.commit()

        return draft

    def _evaluate_auto_send_safety(
        self,
        settings: AICMSettings,
        analysis: AIAnalysisResult,
        reply_result: AIReplyResult,
        platform: str,
    ) -> tuple[bool, str | None]:
        """
        Enforces Section 8 strict rules against automatic sending.
        """
        # Rule 1: Human intervention explicitly required
        if analysis.requires_human or reply_result.requires_human:
            return False, "Intervention humaine requise par l'analyse ou la génération"

        # Rule 2: Minimum confidence score
        if reply_result.confidence < settings.min_confidence_score:
            return False, f"Score de confiance ({reply_result.confidence:.2f}) inférieur au seuil requis ({settings.min_confidence_score:.2f})"

        # Rule 3: Blocked intents (complaint, refund, threat, legal, payment, spam)
        intent_str = analysis.intent.value if hasattr(analysis.intent, "value") else str(analysis.intent)
        blocked = [b.lower() for b in (settings.blocked_intents or [])]
        if intent_str.lower() in blocked:
            return False, f"Intention '{intent_str}' interdite pour l'envoi automatique"

        # Rule 4: Negative sentiment is NEVER sent automatically
        if analysis.sentiment == SentimentType.NEGATIVE:
            return False, "Sentiment négatif détecté : envoi automatique interdit"

        # Rule 5: Platform must be allowed
        enabled_platforms = [p.lower() for p in (settings.enabled_platforms or [])]
        if platform.lower() not in enabled_platforms:
            return False, f"Plateforme '{platform}' non autorisée pour l'envoi automatique"

        # Rule 6: Language must be authorized
        if analysis.language and settings.allowed_languages:
            if analysis.language.lower() not in [l.lower() for l in settings.allowed_languages]:
                return False, f"Langue '{analysis.language}' non autorisée pour l'automatisation"

        # Rule 7: Intent must be in auto_reply_intents
        allowed_intents = [i.lower() for i in (settings.auto_reply_intents or [])]
        if intent_str.lower() not in allowed_intents:
            return False, f"Intention '{intent_str}' non incluse dans la liste autorisée"

        # Rule 8: Missing sources / unknown info
        if not reply_result.sources_used:
            return False, "Aucune source interne vérifiée n'a pu justifier la réponse"

        return True, None

    def _dispatch_draft(
        self,
        db: Session,
        draft: AIReplyDraft,
        message: InboxMessage,
        is_automatic: bool = False,
        actor_user_id: int | None = None,
    ) -> None:
        """
        Internal worker to send reply via social platform and record audit state.
        """
        try:
            ext_reply_id = self.social_service.send_social_reply(
                db=db,
                workspace_id=draft.workspace_id,
                message=message,
                content=draft.reply_text,
            )

            now = datetime.now(UTC)
            draft.status = AIReplyDraftStatus.SENT
            draft.sent_at = now
            draft.external_reply_id = ext_reply_id
            draft.error_message = None

            # Update message
            message.replied_at = now
            message.is_resolved = True
            message.is_read = True

            db.commit()

            # Record audit
            db.add(AICMAuditLog(
                workspace_id=draft.workspace_id,
                inbox_message_id=message.id,
                user_id=actor_user_id,
                action="AUTO_SEND" if is_automatic else "SEND_REPLY",
                details={
                    "draft_id": draft.id,
                    "external_reply_id": ext_reply_id,
                    "is_automatic": is_automatic,
                    "content": draft.reply_text[:100],
                },
            ))
            db.commit()

        except Exception as exc:
            logger.error(
                "AutoReplyService: Failed to dispatch reply for draft %s: %s",
                draft.id,
                exc,
            )
            draft.status = AIReplyDraftStatus.FAILED
            draft.error_message = str(exc)
            db.commit()

            db.add(AICMAuditLog(
                workspace_id=draft.workspace_id,
                inbox_message_id=message.id,
                user_id=actor_user_id,
                action="SEND_FAILED",
                details={
                    "draft_id": draft.id,
                    "error": str(exc),
                },
            ))
            db.commit()
            if not is_automatic:
                raise

    def approve_draft(
        self,
        db: Session,
        workspace_id: int,
        draft_id: int,
        approved: bool,
        modified_reply_text: str | None = None,
        auto_send: bool = True,
        actor_user_id: int | None = None,
    ) -> AIReplyDraft:
        """
        Human reviewer approves or rejects an AI suggested draft.
        """
        draft = (
            db.query(AIReplyDraft)
            .filter(
                AIReplyDraft.id == draft_id,
                AIReplyDraft.workspace_id == workspace_id,
            )
            .first()
        )
        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brouillon de réponse introuvable.")

        message = db.get(InboxMessage, draft.inbox_message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message lié introuvable.")

        now = datetime.now(UTC)
        draft.reviewed_by_user_id = actor_user_id
        draft.reviewed_at = now

        if not approved:
            draft.status = AIReplyDraftStatus.REJECTED
            db.commit()
            db.refresh(draft)

            db.add(AICMAuditLog(
                workspace_id=workspace_id,
                inbox_message_id=message.id,
                user_id=actor_user_id,
                action="REJECT_DRAFT",
                details={"draft_id": draft.id},
            ))
            db.commit()
            return draft

        # If modified text provided
        if modified_reply_text and modified_reply_text.strip():
            draft.reply_text = modified_reply_text.strip()

        draft.status = AIReplyDraftStatus.APPROVED
        db.commit()
        db.refresh(draft)

        db.add(AICMAuditLog(
            workspace_id=workspace_id,
            inbox_message_id=message.id,
            user_id=actor_user_id,
            action="APPROVE_DRAFT",
            details={
                "draft_id": draft.id,
                "was_modified": draft.reply_text != draft.original_reply_text,
                "auto_send": auto_send,
            },
        ))
        db.commit()

        # If auto_send is requested upon human approval, dispatch immediately
        if auto_send:
            self._dispatch_draft(db, draft, message, is_automatic=False, actor_user_id=actor_user_id)
            db.refresh(draft)

        return draft
