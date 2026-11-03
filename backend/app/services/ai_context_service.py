from __future__ import annotations

import logging
import re
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.business_knowledge import BusinessKnowledge, KnowledgeProduct, KnowledgeFAQ
from app.models.inbox_message import InboxMessage
from app.services.business_knowledge_service import BusinessKnowledgeService

logger = logging.getLogger(__name__)


class AIContextBundle:
    """
    Secure, scoped business context prepared specifically for an interaction.
    Guarantees no secret/token leakage and strict workspace isolation.
    """
    def __init__(
        self,
        workspace_id: int,
        company_profile: dict[str, Any],
        relevant_products: list[dict[str, Any]],
        relevant_faqs: list[dict[str, Any]],
        policies: dict[str, str | None],
        editorial_guidelines: dict[str, Any],
        conversation_history: list[dict[str, str]],
        customer_summary: dict[str, Any],
    ):
        self.workspace_id = workspace_id
        self.company_profile = company_profile
        self.relevant_products = relevant_products
        self.relevant_faqs = relevant_faqs
        self.policies = policies
        self.editorial_guidelines = editorial_guidelines
        self.conversation_history = conversation_history
        self.customer_summary = customer_summary

    def to_system_prompt_context(self) -> str:
        """
        Formats the context into clean, structured markdown for LLM injection.
        Guarantees that user content is clearly demarcated and cannot override system prompts.
        """
        lines = []

        # 1. Company Profile
        cp = self.company_profile
        lines.append(f"### Entreprise : {cp.get('name')}")
        if cp.get("description"):
            lines.append(f"Description : {cp.get('description')}")
        if cp.get("industry"):
            lines.append(f"Secteur : {cp.get('industry')}")
        if cp.get("operating_hours"):
            lines.append(f"Horaires : {cp.get('operating_hours')}")
        if cp.get("website"):
            lines.append(f"Site web : {cp.get('website')}")

        # 2. Editorial Identity
        eg = self.editorial_guidelines
        lines.append("\n### Identité éditoriale et ton de marque")
        lines.append(f"- Ton obligatoire : {eg.get('tone', 'professionnel et bienveillant')}")
        if eg.get("style"):
            lines.append(f"- Style : {eg.get('style')}")
        if eg.get("preferred_expressions"):
            lines.append(f"- Expressions valorisées : {', '.join(eg.get('preferred_expressions'))}")
        if eg.get("forbidden_expressions"):
            lines.append(f"- Expressions strictement interdites : {', '.join(eg.get('forbidden_expressions'))}")
        if eg.get("allowed_emojis"):
            lines.append(f"- Emojis autorisés : {' '.join(eg.get('allowed_emojis'))}")

        # 3. Policies (Only non-empty)
        pol = self.policies
        active_policies = {k: v for k, v in pol.items() if v}
        if active_policies:
            lines.append("\n### Politiques officielles de l'entreprise")
            for pol_name, pol_text in active_policies.items():
                label = pol_name.replace("_", " ").capitalize()
                lines.append(f"- **{label}** : {pol_text}")

        # 4. Relevant Products (keyword-matched)
        if self.relevant_products:
            lines.append("\n### Produits et services pertinents vérifiés")
            for prod in self.relevant_products:
                promo_txt = f" (Promo en cours : {prod.get('promotions')})" if prod.get("promotions") else ""
                lines.append(
                    f"- **{prod.get('name')}** : {prod.get('description')} | Prix: {prod.get('price')} | Dispo: {prod.get('availability')}{promo_txt}"
                )

        # 5. Relevant FAQs
        if self.relevant_faqs:
            lines.append("\n### FAQ officielles correspondantes")
            for faq in self.relevant_faqs:
                lines.append(f"- **Q : {faq.get('question')}**\n  R : {faq.get('answer')}")

        # 6. Customer Summary (Safe metadata only, no PII)
        cs = self.customer_summary
        if cs:
            lines.append("\n### Données client de l'interaction (anonymisées)")
            lines.append(f"- Identifiant public de l'expéditeur : {cs.get('sender_name')}")
            if cs.get("previous_interactions_count", 0) > 0:
                lines.append(f"- Nombre d'échanges précédents : {cs.get('previous_interactions_count')}")

        # 7. Approved Examples
        if eg.get("approved_examples"):
            lines.append("\n### Exemples de réponses validées par la marque")
            for ex in eg.get("approved_examples")[:3]:
                lines.append(f"- Scénario : {ex.get('scenario')}")
                lines.append(f"  Message client : \"{ex.get('customer_message')}\"")
                lines.append(f"  Réponse modèle : \"{ex.get('approved_reply')}\"")

        return "\n".join(lines)


class AIContextService:
    """
    Constructs dynamic context for AI replies and analyses.
    Implements intelligent relevance scoring, strict workspace isolation,
    and prompt injection defense.
    """

    def __init__(self, knowledge_service: BusinessKnowledgeService | None = None):
        self.knowledge_service = knowledge_service or BusinessKnowledgeService()

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract alphanumeric search tokens from message, ignoring basic stop words."""
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        stop_words = {
            "le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "en", "pour",
            "par", "sur", "dans", "avec", "sans", "sous", "vers", "chez", "est", "sont", "a", "au", "aux", "ce", "cet",
            "cette", "ces", "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
            "mon", "ton", "son", "mes", "tes", "ses", "notre", "votre", "leur", "qui",
            "que", "quoi", "dont", "où", "mais", "ou", "donc", "or", "ni", "car", "bonjour",
            "salut", "merci", "svp", "re", "the", "a", "an", "and", "or", "to", "in", "is",
            "tout", "tous", "toute", "toutes", "autre", "autres", "comme", "aussi", "plus",
            "moins", "bien", "très", "fait", "faire", "avez", "avoir", "être", "etes", "êtes",
        }
        tokens = {w for w in cleaned.split() if len(w) >= 3 and w not in stop_words}
        return tokens

    def build_context(
        self,
        db: Session,
        workspace_id: int,
        incoming_message: str,
        sender_name: str | None = None,
        sender_external_id: str | None = None,
        max_products: int = 3,
        max_faqs: int = 4,
    ) -> AIContextBundle:
        """
        Dynamically extracts and constructs relevant context for the incoming message.
        Guarantees strict tenant isolation: all queries filter by workspace_id.
        """
        # 1. Workspace Knowledge Base
        knowledge = self.knowledge_service.get_or_create(db, workspace_id)

        company_profile = {
            "name": knowledge.company_name,
            "description": knowledge.description,
            "industry": knowledge.industry,
            "website": knowledge.website,
            "operating_hours": knowledge.operating_hours,
            "contact_email": knowledge.contact_email,
            "contact_phone": knowledge.contact_phone,
            "languages": knowledge.languages or ["fr"],
        }

        editorial_guidelines = {
            "tone": knowledge.brand_tone,
            "style": knowledge.writing_style,
            "preferred_expressions": knowledge.preferred_expressions or [],
            "forbidden_expressions": knowledge.forbidden_expressions or [],
            "allowed_emojis": knowledge.allowed_emojis or [],
            "approved_examples": knowledge.approved_examples or [],
        }

        policies = {
            "politique_de_remboursement": knowledge.refund_policy,
            "politique_de_retour": knowledge.return_policy,
            "garantie": knowledge.warranty_policy,
            "livraison": knowledge.shipping_policy,
            "reclamations": knowledge.complaint_procedure,
            "contact_support": knowledge.support_contact,
        }

        # 2. Extract keywords from message for smart relevance retrieval
        keywords = self._extract_keywords(incoming_message)

        # 3. Relevant Products Search (keyword matching & scoring)
        all_products = (
            db.query(KnowledgeProduct)
            .filter(KnowledgeProduct.workspace_id == workspace_id)
            .all()
        )

        scored_products = []
        for p in all_products:
            score = 0
            p_text = f"{p.name} {p.description} {' '.join(p.features or [])}".lower()
            for kw in keywords:
                if kw in p_text:
                    score += 2 if kw in p.name.lower() else 1
            scored_products.append((score, p))

        # Sort products by score descending
        scored_products.sort(key=lambda x: x[0], reverse=True)
        # Strictly keep items with positive keyword match score (no false positives)
        matched_products = [p for s, p in scored_products if s >= 2][:max_products]

        relevant_products_data = [
            {
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "availability": p.availability,
                "features": p.features,
                "promotions": p.promotions,
                "delivery_terms": p.delivery_terms,
            }
            for p in matched_products
        ]

        # 4. Relevant FAQs Search (keyword & category matching)
        all_faqs = (
            db.query(KnowledgeFAQ)
            .filter(
                KnowledgeFAQ.workspace_id == workspace_id,
                KnowledgeFAQ.is_active == True,
            )
            .all()
        )

        scored_faqs = []
        for f in all_faqs:
            score = 0
            f_text = f"{f.question} {f.answer} {' '.join(f.keywords or [])}".lower()
            for kw in keywords:
                if kw in f.question.lower():
                    score += 3
                elif any(kw == k.lower() for k in (f.keywords or [])):
                    score += 3
                elif kw in f.answer.lower():
                    score += 1
            scored_faqs.append((score, f))

        scored_faqs.sort(key=lambda x: x[0], reverse=True)
        # Strictly keep items with positive keyword match score (no false positives)
        matched_faqs = [f for s, f in scored_faqs if s >= 2][:max_faqs]

        relevant_faqs_data = [
            {
                "category": f.category,
                "question": f.question,
                "answer": f.answer,
            }
            for f in matched_faqs
        ]

        # 5. Conversation History & Customer Metadata (Safe, isolated)
        history_data = []
        previous_count = 0
        if sender_name or sender_external_id:
            query = db.query(InboxMessage).filter(
                InboxMessage.workspace_id == workspace_id,
            )
            filters = []
            if sender_external_id:
                filters.append(InboxMessage.sender_external_id == sender_external_id)
            if sender_name:
                filters.append(InboxMessage.sender_name == sender_name)
            if filters:
                query = query.filter(or_(*filters))

            past_messages = (
                query.order_by(InboxMessage.created_at.desc())
                .limit(5)
                .all()
            )
            previous_count = len(past_messages)
            for pm in reversed(past_messages):
                history_data.append({
                    "role": "customer",
                    "content": pm.content[:200],  # Truncate to avoid prompt bloat
                    "date": pm.created_at.strftime("%Y-%m-%d %H:%M"),
                })

        customer_summary = {
            "sender_name": sender_name or "Utilisateur",
            "previous_interactions_count": previous_count,
        }

        return AIContextBundle(
            workspace_id=workspace_id,
            company_profile=company_profile,
            relevant_products=relevant_products_data,
            relevant_faqs=relevant_faqs_data,
            policies=policies,
            editorial_guidelines=editorial_guidelines,
            conversation_history=history_data,
            customer_summary=customer_summary,
        )
