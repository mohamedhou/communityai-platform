# AI Community Manager - Guide d'Architecture et d'Utilisation

Le module **AI Community Manager** de CommunityAI est un système intelligent d'automatisation et d'assistance au community management. Il analyse en temps réel les commentaires et les messages privés provenant des réseaux sociaux (Meta Instagram / Facebook, LinkedIn), comprend les besoins des clients à partir de la base de connaissances propre à chaque entreprise, et génère des réponses contextualisées, personnalisées et strictement factuelles.

---

## 1. Vue d'Ensemble de l'Architecture

Le module est structuré autour de composants modulaires et sécurisés avec isolation stricte multi-tenant :

```text
[Webhook Social (Meta/LinkedIn)] ---> [Signature Verification & Deduplication]
                                                     |
                                                     v
[Social Message Dispatch] <---------------- [AutoReplyService]
         ^                                    |           |
         |                            (Mode Auto)   (Mode Approbation)
         |                                    |           |
         |                             [Safety Checks]    v
         |                                    |       [Draft Review UI]
         |                                    v           |
[Meta Graph / LinkedIn API] <-------- [Direct Send]  [Human Validate / Edit]
                                              ^
                                              |
[AI Context Service] ----------------> [AI Reply Engine]
(Keyword matching + Knowledge isolation)      ^
                                              |
[Business Knowledge Base] ----------> [AI Analysis Engine]
(Identity, Products, Policies, Tone)   (Sentiment, Intent, Anti-Injection)
```

---

## 2. Base de Connaissances Entreprise (Business Knowledge Base)

Chaque espace de travail (`Workspace`) dispose d'une base de connaissances dédiée garantissant qu'aucune information ne fuite entre clients.

### 4 Volets Stratégiques :
1. **Identité de l'entreprise (`BusinessKnowledge`)** :
   - Nom, secteur d'activité, site web, description de l'entreprise.
   - Valeurs fondamentales et cibles prioritaires.
2. **Catalogue de Produits et Services (`KnowledgeProduct`)** :
   - Nom du produit/service, catégorie, prix ou fourchette tarifaire.
   - Description détaillée, points forts et arguments de vente.
   - Disponibilité en stock, lien URL direct, mots-clés de déclenchement.
3. **Politiques de Service Client & FAQ (`KnowledgeFAQ`)** :
   - Délais de livraison et transporteurs partenaires.
   - Modalités de retour, échange et politique stricte de remboursement.
   - Canaux de support officiels (email de support, téléphone, horaires d'ouverture).
   - Questions fréquentes et réponses officielles validées.
4. **Identité Éditoriale & Ligne de Conduite (`BusinessKnowledge`)** :
   - Ton de la marque (professionnel, bienveillant, décontracté, technique...).
   - Tutoiement ou vouvoiement systématique.
   - Utilisation modérée ou dynamique des émojis.
   - Liste noire de termes et sujets interdits (mots tabous, concurrents, promesses non tenues).
   - Signatures personnalisées de l'équipe de support.

---

## 3. Moteur d'Analyse des Messages (`AIAnalysisService`)

Dès réception d'une interaction sociale, le moteur applique une analyse structurée :

- **Détection du sentiment** : `POSITIVE`, `NEUTRAL`, `NEGATIVE`.
- **Classification de l'intention** :
  - `QUESTION_PRODUCT` : Demande sur un produit, caractéristiques, disponibilité.
  - `QUESTION_PRICE` : Demande de tarif ou devis.
  - `SUPPORT_REQUEST` : Demande d'assistance technique ou de suivi.
  - `COMPLAINT` : Réclamation, insatisfaction client, litige.
  - `PRAISE` : Remerciements, compliments, avis positif.
  - `FEEDBACK` : Suggestion d'amélioration ou retour d'expérience.
  - `SPAM` : Message publicitaire non sollicité ou bot.
  - `OTHER` : Autre sujet général.
- **Évaluation de l'urgence** : `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- **Détection de la langue** : Code ISO (ex: `fr`, `en`, `es`).
- **Identification du besoin client** : Résumé en une phrase du besoin réel.
- **Détection du niveau de risque et critères d'escalade humaine (`requires_human`)** :
  - Problèmes juridiques, menaces de poursuite, mentions d'avocat.
  - Réclamations sévères et demandes de remboursement complexes.
  - Violations de conformité ou failles de sécurité.
- **Protection Anti-Injection de Prompt** :
  - Neutralisation des tentatives de manipulation de prompt (`"Ignore previous instructions"`, `"System reset"`, balises XML/Markdown malveillantes).
  - Encapsulation hermétique des messages utilisateurs dans des balises de données sécurisées.

---

## 4. Moteur de Contexte et RAG Local (`AIContextService`)

Pour éliminer tout risque d'hallucination :
- **Recherche par mots-clés ciblée** : Analyse lexicale des termes du message client pour extraire uniquement les produits et FAQs pertinents du workspace courant.
- **Grounding Factuel Absolu** : Le prompt système interdit formellement d'inventer des prix, des fonctionnalités absentes ou des politiques non documentées.
- **Gestion des informations manquantes** : Si une information n'est pas renseignée dans la base de connaissances, l'IA formule une réponse courtoise expliquant qu'elle transmet la demande à l'équipe, et signale le draft avec `contains_missing_info=True`.

---

## 5. Moteur de Génération de Réponses (`AIReplyService`)

Prend en charge 9 méthodes métier spécialisées :
1. `analyze_message(text, platform)` : Analyse complète sentiment/intention/urgence.
2. `detect_intent(text)` : Identification isolée de l'intention.
3. `detect_sentiment(text)` : Analyse isolée du sentiment.
4. `generate_reply(message_text, context, history)` : Production d'un brouillon ancré dans les données de l'entreprise avec citation des sources.
5. `improve_reply(reply_text, instruction)` : Raffinement stylistique selon directives spécifiques.
6. `translate_reply(reply_text, target_language)` : Traduction contextuelle préservant le ton de marque.
7. `summarize_conversation(messages)` : Synthèse claire d'un fil d'échange client.
8. `classify_priority(message_text, intent, sentiment)` : Qualification de priorité opérationnelle.
9. `suggest_human_action(message_text, analysis)` : Recommandation d'action pour le gestionnaire de communauté.

---

## 6. Modes d'Automatisation et Règles de Sécurité (`AutoReplyService`)

Trois modes de fonctionnement sont configurables au niveau de l'espace de travail :

| Mode | Nom | Comportement |
| :--- | :--- | :--- |
| **Mode 1** | `MANUAL` | L'IA n'intervient que sur demande explicite de l'utilisateur dans l'Inbox. |
| **Mode 2** | `APPROVAL_REQUIRED` *(Défaut)* | L'IA analyse chaque nouveau message et prépare un brouillon de réponse argumenté. Le Community Manager examine, valide ou retouche la réponse avant envoi. |
| **Mode 3** | `AUTOMATIC` | L'IA répond et publie automatiquement **uniquement** si les critères stricts de sécurité ci-dessous sont satisfaits. |

### Safety Blocklist (Verrous de Sécurité Absolus en Mode 3) :
Même si le Mode Automatique est activé, l'envoi direct est **immédiatement bloqué** et basculé en brouillon pour validation humaine dans les cas suivants :
- ❌ **Réclamations et plaintes** (`COMPLAINT`).
- ❌ **Demandes de remboursement ou litiges financiers**.
- ❌ **Menaces, risques de crise ou propos agressifs**.
- ❌ **Score de confiance de l'IA inférieur au seuil minimal configuré** (ex: `< 0.85`).
- ❌ **Informations manquantes dans la base de connaissances** (`contains_missing_info=True`).
- ❌ **Message nécessitant une action humaine** (`requires_human=True`).
- ❌ **En dehors des horaires de travail configurés** (si l'option d'envoi strict en heures ouvrées est activée).

Toutes les décisions (envois, blocages de sécurité, validations, rejets) sont tracées dans la table `aicm_audit_logs`.

---

## 7. Escalade et Assignation d'Équipe (`EscalationService`)

- **Escalade** : Un message sensible peut être escaladé à un manager ou à un référent d'équipe avec note explicative (`POST /api/v1/ai-cm/messages/{id}/escalate`).
- **Assignation** : Attribution ciblée d'un message à un collaborateur du workspace (`POST /api/v1/ai-cm/messages/{id}/assign`).
- **Filtrage dans l'Inbox** : Filtres rapides par intention (`Achat`, `Question prix`, `Réclamation`, `Spam`), par urgence (`Haute`, `Critique`) et filtre `Escaladés`.

---

## 8. Webhooks & Passerelle Réseaux Sociaux

### Configuration Meta (Facebook & Instagram)
1. **Endpoint de vérification (GET)** :
   - URL : `https://ton-domaine.com/api/v1/webhooks/meta`
   - Vérifie le token de challenge `hub.challenge` avec le secret configuré dans `META_WEBHOOK_VERIFY_TOKEN`.
2. **Endpoint de réception (POST)** :
   - URL : `https://ton-domaine.com/api/v1/webhooks/meta`
   - Valide la signature cryptographique d'en-tête `X-Hub-Signature-256` via HMAC-SHA256 avec `META_CLIENT_SECRET`.
   - Traite les commentaires (`changes: comment`) et messages privés (`messaging`).
   - Anti-rejeu : Déduplication en mémoire sur l'identifiant unique d'événement `entry.id` ou `message.mid`.

### Envoi de Réponses Réelles vs Limitations Officielles (`SocialMessageService`)
- **Meta (Facebook & Instagram)** :
  - Réponses aux commentaires publics : `POST https://graph.facebook.com/{version}/{comment_id}/comments` avec paramètre `message`.
  - Réponses aux messages privés : `POST https://graph.facebook.com/{version}/me/messages` (nécessite la permission `pages_messaging` ou `instagram_manage_messages`).
- **LinkedIn** :
  - Commentaires publics de page Entreprise : supporté via `/rest/socialActions/{commentUrn}/comments` avec jeton d'organisation.
  - Messages privés LinkedIn : **Non supporté** par l'API publique standard LinkedIn (réservé aux partenaires certifiés LinkedIn Messaging API). En cas de tentative d'envoi automatique sur un MP LinkedIn, le service consigne une erreur explicite sans planter l'application.

---

## 9. Répertoire des Endpoints API

### Base de Connaissances Entreprise (`/api/v1/business-knowledge`)
| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Récupérer l'identité et les politiques de l'entreprise |
| `PUT` | `/` | Mettre à jour l'identité et les politiques de l'entreprise |
| `POST` | `/seed-defaults` | Initialiser la base de connaissances avec un gabarit complet |
| `GET` | `/products` | Lister les produits / services du workspace |
| `POST` | `/products` | Créer un nouveau produit ou service |
| `PUT` | `/products/{id}` | Modifier un produit existant |
| `DELETE` | `/products/{id}` | Supprimer un produit |
| `GET` | `/faqs` | Lister les FAQs du workspace |
| `POST` | `/faqs` | Ajouter une nouvelle FAQ |
| `PUT` | `/faqs/{id}` | Modifier une FAQ existante |
| `DELETE` | `/faqs/{id}` | Supprimer une FAQ |

### AI Community Manager (`/api/v1/ai-cm`)
| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/settings` | Consulter les paramètres d'automatisation du workspace |
| `PUT` | `/settings` | Modifier les paramètres (mode, seuil de confiance, horaires...) |
| `GET` | `/dashboard` | Consulter les KPIs opérationnels réels (taux d'automatisation, sentiments, intentions...) |
| `GET` | `/audit-logs` | Journal d'audit complet de toutes les actions IA et humaines |
| `POST` | `/messages/{id}/analyze` | Déclencher l'analyse IA d'un message de l'inbox |
| `POST` | `/messages/{id}/generate-reply` | Générer un brouillon ancré dans la base de connaissances |
| `GET` | `/drafts` | Lister les brouillons en attente du workspace |
| `POST` | `/drafts/{id}/approve` | Valider et envoyer un brouillon généré par l'IA |
| `POST` | `/drafts/{id}/reject` | Rejeter un brouillon avec motif |
| `POST` | `/messages/{id}/escalate` | Escalader un message à un manager avec note interne |
| `POST` | `/messages/{id}/assign` | Assigner un message à un membre de l'équipe |
| `GET` | `/messages/{id}/context` | Visualiser le contexte documentaire injecté pour un message |

### Webhooks (`/api/v1/webhooks`)
| Méthode | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/meta` | Vérification du challenge d'abonnement Meta Webhook |
| `POST` | `/meta` | Réception et traitement automatique d'événements Meta |

---

## 10. Prérequis Meta & LinkedIn pour le Déploiement en Production

Pour connecter l'AI Community Manager à des comptes sociaux réels :

### Meta Developer Console
1. Créer une application de type **Business** sur [Meta for Developers](https://developers.facebook.com/).
2. Ajouter les produits **Facebook Login for Business** et **Webhooks**.
3. Autorisations requises (Permissions) :
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `pages_manage_engagement` (pour répondre aux commentaires)
   - `pages_messaging` (pour répondre aux messages privés Messenger)
   - `instagram_basic`, `instagram_manage_comments`, `instagram_manage_messages` (pour Instagram).
4. Configurer le Webhook avec l'URL publique HTTPS du serveur (`/api/v1/webhooks/meta`), le champ d'abonnement `page` ou `instagram`, et le `Verify Token` identique à `META_WEBHOOK_VERIFY_TOKEN`.
5. Passer l'App Review Meta pour la mise en production des permissions avancées.

### LinkedIn Developer Portal
1. Créer une application sur [LinkedIn Developers](https://www.linkedin.com/developers/).
2. Vérifier la page Entreprise LinkedIn associée.
3. Souscrire au produit **Share on LinkedIn** et **Sign In with LinkedIn using OpenID Connect**.
4. Autorisations de commentaires : `w_organization_social` et `r_organization_social`.
