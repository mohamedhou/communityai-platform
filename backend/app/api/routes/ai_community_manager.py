from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.api.dependencies import get_db
from app.api.workspace_context import (
    WorkspaceContext,
    get_workspace_context,
    require_workspace_editor,
)
from app.models.ai_community_manager import (
    AICMMode,
    AICMSettings,
    AIReplyDraft,
    AIReplyDraftStatus,
    AICMAuditLog,
)
from app.models.inbox_message import InboxMessage, InboxMessageType, InboxSentiment
from app.schemas.ai_community_manager import (
    AIAnalysisResult,
    AICMDashboardMetrics,
    AICMSettingsResponse,
    AICMSettingsUpdate,
    AICMAuditLogResponse,
    AIReplyApprovalRequest,
    AIReplyDraftResponse,
    AIReplyResult,
    AIReplySendRequest,
    IntentBreakdown,
    MessageAssignmentRequest,
    MessageEscalationRequest,
    SentimentBreakdown,
)
from app.services.ai_analysis_service import AIAnalysisService
from app.services.ai_context_service import AIContextService
from app.services.ai_reply_service import AIReplyService
from app.services.auto_reply_service import AutoReplyService
from app.services.conversation_service import ConversationService
from app.services.escalation_service import EscalationService
from app.services.social_message_service import SocialMessageService

router = APIRouter(prefix="/api/v1/ai-cm", tags=["ai-community-manager"])

auto_reply_service = AutoReplyService()
analysis_service = AIAnalysisService()
reply_service = AIReplyService()
context_service = AIContextService()
conversation_service = ConversationService()
escalation_service = EscalationService()
social_service = SocialMessageService()


# ==========================================
# Settings Endpoints
# ==========================================

@router.get("/settings", response_model=AICMSettingsResponse)
def get_ai_cm_settings(
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> AICMSettingsResponse:
    """Retrieve automation settings and rules for current workspace."""
    settings = auto_reply_service.get_or_create_settings(db, context.workspace_id)
    return AICMSettingsResponse.model_validate(settings)


@router.patch("/settings", response_model=AICMSettingsResponse)
@router.put("/settings", response_model=AICMSettingsResponse)
def update_ai_cm_settings(
    payload: AICMSettingsUpdate,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> AICMSettingsResponse:
    """Update automation mode, confidence threshold, blocked intents, and schedules."""
    settings = auto_reply_service.get_or_create_settings(db, context.workspace_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "mode" in update_data and update_data["mode"]:
        mode_val = update_data["mode"].upper().strip()
        if mode_val in AICMMode.__members__:
            settings.mode = AICMMode[mode_val]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mode invalide. Choix possibles : {list(AICMMode.__members__.keys())}",
            )
        del update_data["mode"]

    for key, value in update_data.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)

    # Audit settings update
    db.add(AICMAuditLog(
        workspace_id=context.workspace_id,
        user_id=context.user.id,
        action="UPDATE_SETTINGS",
        details={"mode": settings.mode.value, "min_confidence": settings.min_confidence_score},
    ))
    db.commit()

    return AICMSettingsResponse.model_validate(settings)


# ==========================================
# Dashboard & Analytics Endpoints
# ==========================================

@router.get("/dashboard", response_model=AICMDashboardMetrics)
def get_dashboard_metrics(
    platform: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> AICMDashboardMetrics:
    """
    Computes real, non-simulated operational metrics for the AI Community Manager dashboard.
    """
    workspace_id = context.workspace_id

    # Messages query
    msg_query = db.query(InboxMessage).filter(InboxMessage.workspace_id == workspace_id)
    if platform:
        from app.social.models import SocialAccount
        msg_query = msg_query.join(SocialAccount).filter(SocialAccount.platform == platform)
    if start_date:
        msg_query = msg_query.filter(InboxMessage.created_at >= start_date)
    if end_date:
        msg_query = msg_query.filter(InboxMessage.created_at <= end_date)

    all_messages = msg_query.all()
    total_count = len(all_messages)

    comments_count = sum(1 for m in all_messages if m.type == InboxMessageType.COMMENT)
    messages_count = sum(1 for m in all_messages if m.type in (InboxMessageType.MESSAGE, InboxMessageType.MENTION))
    urgent_count = sum(1 for m in all_messages if m.urgency in ("high", "critical"))
    escalated_count = sum(1 for m in all_messages if m.is_escalated)
    resolved_count = sum(1 for m in all_messages if m.is_resolved)

    resolution_rate = round((resolved_count / total_count * 100.0), 1) if total_count > 0 else 0.0

    # Calculate average response time in seconds
    replied_times = [
        (m.replied_at - m.created_at).total_seconds()
        for m in all_messages
        if m.replied_at and m.created_at and m.replied_at >= m.created_at
    ]
    avg_response_time = round(sum(replied_times) / len(replied_times), 1) if replied_times else None

    # Sentiment Breakdown
    sentiment_bd = SentimentBreakdown(
        positive=sum(1 for m in all_messages if m.sentiment == InboxSentiment.POSITIVE),
        neutral=sum(1 for m in all_messages if m.sentiment == InboxSentiment.NEUTRAL or m.sentiment == InboxSentiment.UNKNOWN),
        negative=sum(1 for m in all_messages if m.sentiment == InboxSentiment.NEGATIVE),
    )

    # Intent Breakdown
    intent_bd = IntentBreakdown(
        question=sum(1 for m in all_messages if m.intent == "question"),
        purchase=sum(1 for m in all_messages if m.intent == "purchase"),
        price_inquiry=sum(1 for m in all_messages if m.intent == "price_inquiry"),
        complaint=sum(1 for m in all_messages if m.intent == "complaint"),
        compliment=sum(1 for m in all_messages if m.intent == "compliment"),
        delivery_inquiry=sum(1 for m in all_messages if m.intent == "delivery_inquiry"),
        support_request=sum(1 for m in all_messages if m.intent == "support_request"),
        spam=sum(1 for m in all_messages if m.intent == "spam"),
    )

    # Drafts query
    draft_query = db.query(AIReplyDraft).filter(AIReplyDraft.workspace_id == workspace_id)
    if start_date:
        draft_query = draft_query.filter(AIReplyDraft.created_at >= start_date)
    if end_date:
        draft_query = draft_query.filter(AIReplyDraft.created_at <= end_date)

    all_drafts = draft_query.all()
    replies_generated = len(all_drafts)
    replies_sent = sum(1 for d in all_drafts if d.status == AIReplyDraftStatus.SENT)
    replies_pending = sum(1 for d in all_drafts if d.status == AIReplyDraftStatus.SUGGESTED)

    return AICMDashboardMetrics(
        total_comments_analyzed=comments_count,
        total_messages_analyzed=messages_count,
        replies_generated=replies_generated,
        replies_sent=replies_sent,
        replies_pending_approval=replies_pending,
        urgent_messages_count=urgent_count,
        escalated_conversations_count=escalated_count,
        resolution_rate=resolution_rate,
        average_response_time_seconds=avg_response_time,
        sentiment_breakdown=sentiment_bd,
        intent_breakdown=intent_bd,
    )


# ==========================================
# Audit Trail Endpoints
# ==========================================

@router.get("/audit-logs", response_model=list[AICMAuditLogResponse])
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None),
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[AICMAuditLogResponse]:
    """Retrieve audit history of AI evaluations, approvals, and dispatches."""
    query = db.query(AICMAuditLog).filter(AICMAuditLog.workspace_id == context.workspace_id)
    if action:
        query = query.filter(AICMAuditLog.action == action)
    logs = query.order_by(AICMAuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return [AICMAuditLogResponse.model_validate(l) for l in logs]


# ==========================================
# Drafts & Reply Approval Endpoints
# ==========================================

@router.get("/drafts", response_model=list[AIReplyDraftResponse])
def list_drafts(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[AIReplyDraftResponse]:
    """List AI reply drafts with optional status filter."""
    query = db.query(AIReplyDraft).filter(AIReplyDraft.workspace_id == context.workspace_id)
    if status:
        query = query.filter(AIReplyDraft.status == status)
    drafts = query.order_by(AIReplyDraft.created_at.desc()).offset(offset).limit(limit).all()
    return [AIReplyDraftResponse.model_validate(d) for d in drafts]


@router.get("/drafts/{draft_id}", response_model=AIReplyDraftResponse)
def get_draft(
    draft_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> AIReplyDraftResponse:
    """Get single reply draft."""
    draft = db.query(AIReplyDraft).filter(
        AIReplyDraft.id == draft_id,
        AIReplyDraft.workspace_id == context.workspace_id,
    ).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brouillon introuvable.")
    return AIReplyDraftResponse.model_validate(draft)


@router.post("/drafts/{draft_id}/approve", response_model=AIReplyDraftResponse)
def approve_draft(
    draft_id: int,
    payload: AIReplyApprovalRequest,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> AIReplyDraftResponse:
    """Approve or reject draft reply with optional text modification."""
    draft = auto_reply_service.approve_draft(
        db=db,
        workspace_id=context.workspace_id,
        draft_id=draft_id,
        approved=payload.approved,
        modified_reply_text=payload.modified_reply_text,
        auto_send=payload.auto_send,
        actor_user_id=context.user.id,
    )
    return AIReplyDraftResponse.model_validate(draft)


# ==========================================
# Message Interactive Endpoints (Analyze, Generate, Context, History, Escalate)
# ==========================================

@router.post("/messages/{message_id}/analyze", response_model=AIAnalysisResult)
def analyze_message_endpoint(
    message_id: int,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> AIAnalysisResult:
    """Run structured AI analysis on an existing inbox interaction."""
    msg = db.query(InboxMessage).filter(
        InboxMessage.id == message_id,
        InboxMessage.workspace_id == context.workspace_id,
    ).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable.")

    platform_str = "social"
    if msg.social_account:
        platform_str = msg.social_account.platform or msg.social_account.provider or "social"

    analysis = analysis_service.analyze_message(
        content=msg.content,
        sender_name=msg.sender_name,
        platform=platform_str,
    )

    # Update message
    msg.intent = analysis.intent.value if hasattr(analysis.intent, "value") else str(analysis.intent)
    msg.urgency = analysis.urgency.value if hasattr(analysis.urgency, "value") else str(analysis.urgency)
    msg.topic = analysis.topic
    msg.language = analysis.language
    msg.ai_analysis = analysis.model_dump()
    db.commit()
    db.refresh(msg)

    return analysis


@router.post("/messages/{message_id}/generate-reply", response_model=AIReplyDraftResponse)
def generate_reply_endpoint(
    message_id: int,
    custom_instructions: str | None = Query(default=None),
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
) -> AIReplyDraftResponse:
    """Generate or regenerate an AI reply suggestion grounded in business knowledge."""
    msg = db.query(InboxMessage).filter(
        InboxMessage.id == message_id,
        InboxMessage.workspace_id == context.workspace_id,
    ).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable.")

    draft = auto_reply_service.process_incoming_interaction(
        db=db,
        workspace_id=context.workspace_id,
        message=msg,
    )
    if not draft:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Impossible de générer le brouillon.")
    return AIReplyDraftResponse.model_validate(draft)


@router.get("/messages/{message_id}/context")
def get_message_context_preview(
    message_id: int,
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve the business context used to generate replies for this message."""
    msg = db.query(InboxMessage).filter(
        InboxMessage.id == message_id,
        InboxMessage.workspace_id == context.workspace_id,
    ).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message introuvable.")

    bundle = context_service.build_context(
        db=db,
        workspace_id=context.workspace_id,
        incoming_message=msg.content,
        sender_name=msg.sender_name,
        sender_external_id=msg.sender_external_id,
    )

    return {
        "company_profile": bundle.company_profile,
        "relevant_products": bundle.relevant_products,
        "relevant_faqs": bundle.relevant_faqs,
        "policies": bundle.policies,
        "editorial_guidelines": bundle.editorial_guidelines,
        "customer_summary": bundle.customer_summary,
    }


@router.get("/messages/{message_id}/history")
def get_conversation_history(
    message_id: int,
    limit: int = Query(default=20, ge=1, le=50),
    context: WorkspaceContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Retrieve full chronological conversation thread for this customer/sender."""
    return conversation_service.get_conversation_history(
        db=db,
        workspace_id=context.workspace_id,
        message_id=message_id,
        limit=limit,
    )


@router.post("/messages/{message_id}/escalate")
def escalate_message_endpoint(
    message_id: int,
    payload: MessageEscalationRequest,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
):
    """Escalate a message to a manager or default escalation lead."""
    escalated = escalation_service.escalate_message(
        db=db,
        workspace_id=context.workspace_id,
        message_id=message_id,
        note=payload.escalation_note,
        escalated_to_user_id=payload.escalated_to_user_id,
        actor_user_id=context.user.id,
    )
    return {
        "status": "escalated",
        "message_id": escalated.id,
        "escalated_to_user_id": escalated.escalated_to_user_id,
        "escalation_note": escalated.escalation_note,
        "escalated_at": escalated.escalated_at.isoformat() if escalated.escalated_at else None,
    }


@router.post("/messages/{message_id}/assign")
def assign_message_endpoint(
    message_id: int,
    payload: MessageAssignmentRequest,
    context: WorkspaceContext = Depends(require_workspace_editor),
    db: Session = Depends(get_db),
):
    """Assign or reassign an interaction to a specific team member."""
    assigned = escalation_service.assign_message(
        db=db,
        workspace_id=context.workspace_id,
        message_id=message_id,
        assigned_to_user_id=payload.assigned_to_user_id,
        actor_user_id=context.user.id,
    )
    return {
        "status": "assigned",
        "message_id": assigned.id,
        "assigned_to_user_id": assigned.assigned_to_user_id,
    }
