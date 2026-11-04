# CommunityAI - Architecture Technique Globale

Ce document présente l'architecture technique, logicielle, et sécuritaire de la plateforme **CommunityAI**, développée dans le cadre d'un projet de fin d'études / stage de Master.

---

## 1. Vue d'Ensemble du Système

CommunityAI est une plateforme SaaS multi-tenant conçue pour centraliser et automatiser le community management sur les réseaux sociaux (Meta Instagram/Facebook, LinkedIn) avec un assistant IA local souverain et sécurisé.

```text
+-------------------------------------------------------------------------------+
|                                FRONTEND (SPA)                                 |
|   React 18 / TypeScript / Vite / TailwindCSS / Lucide-React / TanStack Query  |
|                                                                               |
|   [Auth / Login]  [Dashboard]  [Calendar & Posts]  [Inbox & AI Suggestions]   |
|   [Business Knowledge]  [AI CM Settings]  [Audit Logs]  [Analytics]           |
+-------------------------------------------------------------------------------+
                                        |
                            HTTP / REST / Webhooks
                                        |
+-------------------------------------------------------------------------------+
|                               BACKEND (FastAPI)                               |
|                                                                               |
|  +------------------------ API Routers (/api/v1) --------------------------+  |
|  | /auth          /users            /workspaces         /posts             |  |
|  | /calendar      /inbox            /analytics          /media             |  |
|  | /notifications /settings         /social-accounts    /webhooks          |  |
|  | /business-knowledge              /ai-cm                                 |  |
|  +-------------------------------------------------------------------------+  |
|                                       |                                       |
|  +--------------------------- Couche Services -----------------------------+  |
|  | AuthService          WorkspaceService     PostService     InboxService  |  |
|  | AIAnalysisService    AIContextService     AIReplyService  AutoReplySvc  |  |
|  | SocialMessageService WebhookService       AnalyticsSvc    NotificationSvc|  |
|  +-------------------------------------------------------------------------+  |
|                                       |                                       |
|  +------------------- Couche Sécurité & Abstractions ----------------------+  |
|  | - RBAC (Owner, Admin, CM, Client)        - Multi-Tenant Workspace Scope |  |
|  | - Fernet Token Encryption                - HMAC-SHA256 Webhooks         |  |
|  | - JWT Access / Refresh Cookies           - Heuristic Safety Guardrails  |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
           |                                     |                   |
           v                                     v                   v
+-----------------------+              +-------------------+   +---------------+
|     PostgreSQL        |              |       Redis       |   | Ollama Server |
|  - Relational Data    |              |  - Cache          |   |  Local LLM    |
|  - SQLAlchemy Core    |              |  - Deduplication  |   | (llama3.2/    |
|  - 13 Migrations      |              |  - Token blacklist|   |  smollm2)     |
+-----------------------+              +-------------------+   +---------------+
```

---

## 2. Architecture Frontend

- **Framework & Outils** : React 18, TypeScript, Vite, TailwindCSS.
- **Gestion d'État & Requêtes** : TanStack Query (React Query) pour le cache asynchrone, hooks React personnalisés pour l'état local.
- **Routage** : React Router DOM v6 avec protection par routes privées (`ProtectedRoute`) et validation des rôles.
- **Modularité** :
  - `pages/ai-community-manager/` : Tableau de bord AI CM, gestion des brouillons, configuration des 3 modes d'automatisation, journal d'audit.
  - `pages/business-knowledge/` : Gestion de l'identité d'entreprise, catalogue de produits et tarifs, politiques et FAQ, tonalité et règles éditoriales.
  - `pages/inbox/` : Boîte de réception unifiée, visualisation des commentaires et messages, prévisualisation de la réponse IA suggérée et validation humaine.
  - `pages/posts/` & `pages/calendar/` : Création, planification et calendrier éditorial de publication.
  - `pages/analytics/` : Métriques d'engagement, sentiments et graphiques temporels.

---

## 3. Architecture Backend (FastAPI)

Le backend respecte les principes de la Clean Architecture modulaire :

```text
backend/app/
├── api/
│   ├── deps.py               # Injection de dépendances (get_db, get_current_user, RBAC)
│   └── routes/               # 14 modules de routes REST versionnées
├── core/
│   ├── config.py             # Pydantic BaseSettings avec validation stricte
│   └── security.py           # Hachage bcrypt, JWT, chiffrement symétrique Fernet
├── models/                   # Modèles SQLAlchemy déclaratifs
├── schemas/                  # Schémas Pydantic v2 (Input, Output, Enums)
├── services/                 # Logique métier découplée de la persistance
├── ai/                       # Moteurs d'IA (OllamaProvider, MockProvider, OpenAI, Gemini)
└── alembic/                  # Migrations de base de données
```

---

## 4. Pipeline IA & Moteur AI Community Manager

Le module AI Community Manager intègre une chaîne de traitement défensive à haute intégrité :

```text
1. Message entrant (Commentaire / DM social ou Webhook)
                       │
                       ▼
2. AIAnalysisService (Analyse Sémantique & Sécurité)
   ├── Détection sentiment (positive, neutral, negative)
   ├── Classification intention (question, price_inquiry, complaint, compliment, spam...)
   ├── Évaluation de l'urgence (low, normal, high, critical)
   ├── Détection du risque (litige, réputation, churn)
   └── Garde-fous Anti-Injection (détection de mots-clés d'évasion & balisage hermétique)
                       │
                       ▼
3. AIContextService (Recherche RAG & Grounding Factuel)
   ├── Filtrage strict par workspace_id (aucune fuite entre tenants)
   ├── Correspondance sémantique et lexicale sur le catalogue produits et FAQ
   └── Extraction des politiques d'entreprise et de la tonalité éditoriale
                       │
                       ▼
4. AIReplyService (Génération Contextualisée & Factuelle)
   ├── Grounding strict : interdiction d'inventer des prix ou politiques
   ├── Traitement des inconnues : si l'information est absente, drapeau requires_human=True
   └── Respect scrupuleux de la langue (français) et du style de la marque
                       │
                       ▼
5. AutoReplyService (Orchestrateur & Sécurité des 3 Modes)
   ├── Mode 1 : MANUAL (brouillon créé en SUGGESTED, validation humaine obligatoire)
   ├── Mode 2 : APPROVAL_REQUIRED (brouillon en SUGGESTED avec suggestion IA pré-remplie)
   └── Mode 3 : AUTOMATIC (envoi automatique SAUF si Safety Blocklist activée)
         │
         ├── Safety Blocklist : Réclamations, Remboursements, Menaces,
         │                      Plaintes, Détection d'Injection, Urgence Critique
         │                      ──> Forcé en SUGGESTED pour intervention humaine
         │
         └── Si interaction standard validée ──> Envoi via SocialMessageService
                       │
                       ▼
6. Traces & Audit : Inscription immuable dans AICMAuditLog
```

---

## 5. Modélisation des Données & Migrations Alembic

La base de données relationnelle est organisée autour de 13 révisions Alembic séquentielles :

1. `0001_initial_setup` : Utilisateurs et sessions.
2. `0002_create_workspaces` : Espaces de travail et adhésions.
3. `0003_create_social_accounts` : Comptes sociaux connectés et tokens chiffrés.
4. `0004_create_posts` : Publications sociales et planification.
5. `0005_create_inbox_messages` : Messages et commentaires sociaux.
6. `0006_create_analytics_metrics` : Métriques d'engagement et statistiques.
7. `0007_create_notifications` : Alertes et notifications in-app.
8. `0008_create_media_assets` : Fichiers médias et métadonnées.
9. `0009_create_workspace_invitations` : Invitations sécurisées d'équipe.
10. `0010_create_workspace_audit_logs` : Journal d'audit d'espace de travail.
11. `0011_create_content_approvals` : Flux de validation éditoriale des publications.
12. `0012_create_business_knowledge` : Base de connaissances d'entreprise (Identité, Produits, FAQs).
13. `0013_create_ai_community_manager` : Paramètres AI CM, analyses IA, brouillons et journaux d'audit.

### Isolation Multi-Tenant

Toutes les tables métiers (`business_knowledge`, `knowledge_products`, `knowledge_faqs`, `ai_cm_settings`, `ai_reply_drafts`, `ai_cm_audit_logs`, `inbox_messages`, `posts`) portent une clé étrangère non nulle `workspace_id`.
Toute requête SQL effectue obligatoirement un filtrage explicite sur le `workspace_id` courant résolu à partir de l'en-tête de session et vérifié par rapport aux adhésions de l'utilisateur connecté.

---

## 6. Sécurité & Protection des Données

1. **Authentification & Gestion de Session** :
   - Mots de passe hachés avec `bcrypt`.
   - Access tokens JWT (HS256) à courte durée de vie (30 min).
   - Refresh tokens transmis via cookie sécurisé (`HttpOnly`, `SameSite=Lax`).
2. **Contrôle d'Accès Basé sur les Rôles (RBAC)** :
   - `OWNER` : Plein pouvoir d'administration, facturation, suppression de workspace.
   - `ADMIN` : Gestion des membres, configuration IA, publication et approbation.
   - `COMMUNITY_MANAGER` : Création de contenu, gestion Inbox, modification et approbation des brouillons IA.
   - `CLIENT` : Consultation seule, soumission de demandes, écriture bloquée (403 Forbidden).
3. **Chiffrement des Secrets Sociaux** :
   - Les jetons d'accès OAuth (Meta Graph API, LinkedIn REST API) sont chiffrés au repos en base de données avec `Fernet` (chiffrement symétrique AES-128-CBC + HMAC-SHA256).
4. **Sécurité des Webhooks** :
   - Vérification du challenge d'abonnement Meta (`hub.mode`, `hub.challenge`, `hub.verify_token`).
   - Validation de la signature cryptographique HMAC-SHA256 (`X-Hub-Signature-256`) sur le corps brut des requêtes entrantes.
   - Déduplication anti-rejeu des messages basée sur l'identifiant externe unique et le hash de transaction.
5. **Garde-fous IA & Défense en Profondeur** :
   - Neutralisation des injections de prompt via des délimiteurs stricts (`<UNTRUSTED_CUSTOMER_MESSAGE>`).
   - Filtre heuristique déterministe en amont et en aval de la génération.
   - Safety Blocklist interdisant formellement l'envoi autonome sur les réclamations et remboursements.

