from __future__ import annotations

import hashlib
import hmac
import json
import logging
from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import get_settings
from app.models.inbox_message import InboxMessage, InboxMessageType, InboxSentiment
from app.social.models import SocialAccount
from app.services.auto_reply_service import AutoReplyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])
auto_reply_service = AutoReplyService()

# In-memory deduplication cache for recent event IDs
_processed_events: set[str] = set()


def _is_duplicate_event(event_id: str) -> bool:
    if event_id in _processed_events:
        return True
    _processed_events.add(event_id)
    if len(_processed_events) > 5000:
        # Simple cleanup
        _processed_events.clear()
    return False


# ==========================================
# Meta (Facebook / Instagram) Webhook
# ==========================================

@router.get("/meta")
def verify_meta_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
):
    """
    Verification endpoint required by Meta Graph API webhook subscription.
    """
    settings = get_settings()
    expected_token = settings.meta_webhook_verify_token or settings.jwt_secret_key[:32]

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        # Accept verification challenge
        return Response(content=hub_challenge, media_type="text/plain")

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")


@router.post("/meta")
async def receive_meta_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Receives events from Meta (comments, feed, mentions, messages).
    Verifies HMAC SHA-256 signature when secret is configured, prevents duplicate processing.
    """
    raw_body = await request.body()
    settings = get_settings()

    # Signature verification if secret is set and not mock mode
    if settings.meta_client_secret and not settings.social_mock_mode and x_hub_signature_256:
        expected_sig = "sha256=" + hmac.new(
            settings.meta_client_secret.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_hub_signature_256):
            logger.warning("Meta webhook signature verification failed.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body)
    except Exception:
        return {"status": "ignored"}

    # Process entries
    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            val = change.get("value", {})
            item = val.get("item")
            verb = val.get("verb")
            comment_id = val.get("comment_id")

            # Only process additions of comments
            if item == "comment" and verb in ("add", None) and comment_id:
                if _is_duplicate_event(f"meta:{comment_id}"):
                    continue

                message_text = val.get("message", "")
                sender_name = val.get("from", {}).get("name", "Utilisateur Facebook")
                sender_id = val.get("from", {}).get("id")

                # Match with connected SocialAccount
                page_id = entry.get("id")
                account = (
                    db.query(SocialAccount)
                    .filter(SocialAccount.external_account_id == str(page_id))
                    .first()
                )
                if account:
                    # Ingest inbox message
                    inbox_msg = InboxMessage(
                        workspace_id=account.workspace_id,
                        user_id=account.user_id,
                        social_account_id=account.id,
                        external_id=str(comment_id),
                        type=InboxMessageType.COMMENT,
                        sender_name=sender_name,
                        sender_external_id=str(sender_id) if sender_id else None,
                        content=message_text,
                        sentiment=InboxSentiment.UNKNOWN,
                    )
                    db.add(inbox_msg)
                    db.commit()
                    db.refresh(inbox_msg)

                    # Trigger auto-reply pipeline
                    try:
                        auto_reply_service.process_incoming_interaction(
                            db=db,
                            workspace_id=account.workspace_id,
                            message=inbox_msg,
                        )
                    except Exception as exc:
                        logger.error("Error processing incoming interaction: %s", exc)

    return {"status": "ok"}


# ==========================================
# LinkedIn Webhook
# ==========================================

@router.post("/linkedin")
async def receive_linkedin_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receives social action events from LinkedIn.
    """
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except Exception:
        return {"status": "ignored"}

    event_id = payload.get("eventId")
    if event_id and _is_duplicate_event(f"linkedin:{event_id}"):
        return {"status": "already_processed"}

    return {"status": "ok"}
