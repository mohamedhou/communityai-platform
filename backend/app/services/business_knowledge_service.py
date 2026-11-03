from __future__ import annotations

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.business_knowledge import BusinessKnowledge, KnowledgeProduct, KnowledgeFAQ
from app.models.workspace import Workspace
from app.schemas.business_knowledge import (
    BusinessKnowledgeBase,
    BusinessKnowledgeUpdate,
    KnowledgeProductCreate,
    KnowledgeProductUpdate,
    KnowledgeFAQCreate,
    KnowledgeFAQUpdate,
)

logger = logging.getLogger(__name__)


class BusinessKnowledgeService:
    """
    Manages the Business Knowledge Base for workspaces:
    - Company Identity
    - Products & Services Catalogue
    - Customer Service Policies
    - Editorial Brand Guidelines
    """

    def get_or_create(self, db: Session, workspace_id: int) -> BusinessKnowledge:
        knowledge = db.query(BusinessKnowledge).filter(BusinessKnowledge.workspace_id == workspace_id).first()
        if not knowledge:
            # Query workspace to grab default name
            ws = db.get(Workspace, workspace_id)
            company_name = ws.name if ws else f"Workspace {workspace_id}"

            knowledge = BusinessKnowledge(
                workspace_id=workspace_id,
                company_name=company_name,
                description=f"Entreprise {company_name}, spécialisée dans les solutions et services innovants.",
                industry="Technologies & Services",
                website="https://example.com",
                contact_email="support@example.com",
                contact_phone="+33 1 23 45 67 89",
                operating_hours="Lundi au Vendredi de 9h00 à 18h00 CET",
                languages=["fr", "en"],
                refund_policy="Remboursement intégral sous 14 jours après réception du produit en cas d'insatisfaction.",
                return_policy="Retour gratuit sous 30 jours via notre étiquette prépayée téléchargeable depuis l'espace client.",
                warranty_policy="Garantie légale de conformité de 2 ans sur l'ensemble de nos matériels et logiciels.",
                shipping_policy="Livraison standard en 48-72h ouvrées en France métropolitaine, offerte dès 50€ d'achat.",
                complaint_procedure="En cas de problème ou litige, contactez notre support client qui répondra sous 24h ouvrées.",
                support_contact="support@example.com ou formulaire en ligne",
                brand_tone="professionnel, bienveillant, clair et réactif",
                writing_style="Phrases concises, formules de politesse soignées, tutoiement interdit sauf directive contraire.",
                preferred_expressions=[
                    "Nous restons à votre entière disposition",
                    "Ravi de vous aider",
                    "Merci pour votre confiance",
                    "Notre équipe est mobilisée pour vous",
                ],
                forbidden_expressions=[
                    "C'est pas notre faute",
                    "Débrouillez-vous",
                    "Impossible",
                    "Vous avez tort",
                ],
                allowed_emojis=["✨", "👋", "✅", "💡", "📦", "🙏"],
                preferred_languages=["fr", "en"],
                approved_examples=[
                    {
                        "scenario": "Question sur les délais de livraison",
                        "customer_message": "Bonjour, quel est le délai de livraison pour Paris ?",
                        "approved_reply": "Bonjour ! Nos commandes sont expédiées sous 24h et livrées en 48h à 72h ouvrées à Paris. La livraison est offerte dès 50€ d'achat. Très belle journée à vous ! ✨",
                    },
                    {
                        "scenario": "Question sur les retours",
                        "customer_message": "Est-ce que je peux renvoyer un produit si la taille ne convient pas ?",
                        "approved_reply": "Bonjour ! Oui tout à fait, vous disposez de 30 jours pour retourner votre article gratuitement grâce à l'étiquette prépayée de votre espace client. Nous restons à votre disposition ! ✅",
                    },
                ],
            )
            db.add(knowledge)
            db.commit()
            db.refresh(knowledge)
        return knowledge

    def update_knowledge(self, db: Session, workspace_id: int, payload: BusinessKnowledgeUpdate) -> BusinessKnowledge:
        knowledge = self.get_or_create(db, workspace_id)
        update_data = payload.model_dump(exclude_unset=True)

        # Handle approved_examples list of dict/pydantic
        if "approved_examples" in update_data and update_data["approved_examples"] is not None:
            update_data["approved_examples"] = [
                ex if isinstance(ex, dict) else ex.model_dump()
                for ex in update_data["approved_examples"]
            ]

        for key, value in update_data.items():
            setattr(knowledge, key, value)

        db.commit()
        db.refresh(knowledge)
        return knowledge

    # ----------------------------------------------------
    # Products & Services Management
    # ----------------------------------------------------

    def list_products(self, db: Session, workspace_id: int) -> list[KnowledgeProduct]:
        return db.query(KnowledgeProduct).filter(KnowledgeProduct.workspace_id == workspace_id).order_by(KnowledgeProduct.id.asc()).all()

    def get_product(self, db: Session, workspace_id: int, product_id: int) -> KnowledgeProduct:
        product = db.query(KnowledgeProduct).filter(
            KnowledgeProduct.workspace_id == workspace_id,
            KnowledgeProduct.id == product_id,
        ).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produit non trouvé")
        return product

    def create_product(self, db: Session, workspace_id: int, payload: KnowledgeProductCreate) -> KnowledgeProduct:
        product = KnowledgeProduct(
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            availability=payload.availability,
            features=payload.features,
            promotions=payload.promotions,
            delivery_terms=payload.delivery_terms,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def update_product(self, db: Session, workspace_id: int, product_id: int, payload: KnowledgeProductUpdate) -> KnowledgeProduct:
        product = self.get_product(db, workspace_id, product_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)
        db.commit()
        db.refresh(product)
        return product

    def delete_product(self, db: Session, workspace_id: int, product_id: int) -> None:
        product = self.get_product(db, workspace_id, product_id)
        db.delete(product)
        db.commit()

    # ----------------------------------------------------
    # FAQs Management
    # ----------------------------------------------------

    def list_faqs(self, db: Session, workspace_id: int, category: str | None = None) -> list[KnowledgeFAQ]:
        query = db.query(KnowledgeFAQ).filter(KnowledgeFAQ.workspace_id == workspace_id)
        if category:
            query = query.filter(KnowledgeFAQ.category == category)
        return query.order_by(KnowledgeFAQ.id.asc()).all()

    def get_faq(self, db: Session, workspace_id: int, faq_id: int) -> KnowledgeFAQ:
        faq = db.query(KnowledgeFAQ).filter(
            KnowledgeFAQ.workspace_id == workspace_id,
            KnowledgeFAQ.id == faq_id,
        ).first()
        if not faq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ non trouvée")
        return faq

    def create_faq(self, db: Session, workspace_id: int, payload: KnowledgeFAQCreate) -> KnowledgeFAQ:
        faq = KnowledgeFAQ(
            workspace_id=workspace_id,
            category=payload.category,
            question=payload.question,
            answer=payload.answer,
            keywords=payload.keywords,
            is_active=payload.is_active,
        )
        db.add(faq)
        db.commit()
        db.refresh(faq)
        return faq

    def update_faq(self, db: Session, workspace_id: int, faq_id: int, payload: KnowledgeFAQUpdate) -> KnowledgeFAQ:
        faq = self.get_faq(db, workspace_id, faq_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(faq, key, value)
        db.commit()
        db.refresh(faq)
        return faq

    def delete_faq(self, db: Session, workspace_id: int, faq_id: int) -> None:
        faq = self.get_faq(db, workspace_id, faq_id)
        db.delete(faq)
        db.commit()

    def seed_default_items_if_empty(self, db: Session, workspace_id: int) -> None:
        """Seed starter products and FAQs if none exist in this workspace."""
        if db.query(KnowledgeProduct).filter(KnowledgeProduct.workspace_id == workspace_id).count() == 0:
            default_products = [
                KnowledgeProductCreate(
                    name="Abonnement CommunityAI Pro",
                    description="Plateforme tout-en-un pour gérer réseaux sociaux, publications et community management assisté par IA.",
                    price="49€ HT / mois",
                    availability="in_stock",
                    features=["Multi-comptes Meta & LinkedIn", "Génération & Planification IA", "Inbox unifiée et modération"],
                    promotions="Premier mois à -20% avec le code WELCOME20",
                    delivery_terms="Activation instantanée en ligne dès confirmation du paiement",
                ),
                KnowledgeProductCreate(
                    name="Pack CommunityAI Entreprise",
                    description="Offre dédiée aux agences et grandes équipes avec support dédié et modèles personnalisés.",
                    price="Sur devis (à partir de 199€ HT / mois)",
                    availability="on_demand",
                    features=["Workspaces illimités", "Modèles Ollama locaux ou cloud", "SLA garanti 99.9%", "Support prioritaire 24/7"],
                    promotions=None,
                    delivery_terms="Déploiement sous 48h ouvrées avec onboarding dédié",
                ),
            ]
            for p in default_products:
                self.create_product(db, workspace_id, p)

        if db.query(KnowledgeFAQ).filter(KnowledgeFAQ.workspace_id == workspace_id).count() == 0:
            default_faqs = [
                KnowledgeFAQCreate(
                    category="Général",
                    question="Comment fonctionne l'essai gratuit ?",
                    answer="Vous bénéficiez de 14 jours d'essai gratuit sans carte bancaire requise avec accès à l'ensemble des fonctionnalités.",
                    keywords=["essai", "gratuit", "test", "carte", "prix"],
                ),
                KnowledgeFAQCreate(
                    category="Sécurité & Données",
                    question="Mes données sont-elles partagées avec d'autres entreprises ?",
                    answer="Non. Chaque workspace dispose d'une étanchéité stricte. Vos informations et vos modèles d'IA ne sont jamais partagés avec des tiers.",
                    keywords=["sécurité", "isolation", "confidentialité", "données", "partage", "rgpd"],
                ),
                KnowledgeFAQCreate(
                    category="Support & Contact",
                    question="Comment contacter le support technique ?",
                    answer="Notre équipe est joignable du lundi au vendredi de 9h à 18h par email à support@example.com ou via notre chat d'assistance.",
                    keywords=["support", "contact", "aide", "horaires", "téléphone", "email"],
                ),
            ]
            for f in default_faqs:
                self.create_faq(db, workspace_id, f)
