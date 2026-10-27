# Intégration Complète d'Ollama dans CommunityAI

Ce document décrit l'architecture, la configuration et l'utilisation du fournisseur d'intelligence artificielle locale **Ollama** au sein de la plateforme CommunityAI.

---

## 1. Vue d'ensemble de l'Architecture

CommunityAI intègre Ollama comme fournisseur IA local de premier plan, sans clé API payante ni dépendance cloud externe.

```
┌─────────────────────────────────┐
│   Frontend React + TypeScript   │
│   (Vite - http://localhost:5173)│
└────────────────┬────────────────┘
                 │ HTTP (REST + Auth JWT)
                 ▼
┌──────────────────────────────────────────────┐
│   Backend FastAPI (Docker)                   │
│   (communityai-backend:8000)                 │
│                                              │
│   AIService                                  │
│     └── OllamaProvider (app/ai/providers)    │
│           ├── /api/tags  (health & model)    │
│           └── /api/chat  (génération réelle) │
└────────────────┬─────────────────────────────┘
                 │ http://host.docker.internal:11434
                 ▼
┌──────────────────────────────────────────────┐
│   Ollama Engine (Hôte Windows / Docker)      │
│   Port : 11434                               │
│   Modèle : llama3.2:3b                       │
└──────────────────────────────────────────────┘
```

---

## 2. Variables d'Environnement

Dans le fichier `.env` à la racine ou `backend/.env` :

| Variable | Valeur par défaut | Description |
| :--- | :--- | :--- |
| `AI_PROVIDER` | `ollama` | Fournisseur actif (`ollama`, `mock`, `openai`, `gemini`) |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | URL du serveur Ollama accessible depuis le conteneur backend Docker |
| `OLLAMA_MODEL` | `llama3.2:3b` | Modèle de langage utilisé pour les générations |

---

## 3. Compatibilité Docker & Réseau

Pour permettre au conteneur `communityai-backend` d'accéder au service Ollama qui tourne sur la machine hôte :
1. `docker-compose.yml` inclut la directive :
   ```yaml
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```
2. Les volumes de développement sont synchronisés en direct :
   - `./backend/app:/app/app`
   - `./backend/tests:/app/tests`
   - `./frontend/communityai/dist:/app/dist`

---

## 4. Installation et Démarrage d'Ollama

### Option A : Installation officielle Ollama (Recommandée)
1. Télécharger Ollama pour Windows depuis le site officiel : [https://ollama.com/download](https://ollama.com/download).
2. Lancer l'installateur.
3. Télécharger le modèle recommandé dans un terminal :
   ```bash
   ollama pull llama3.2:3b
   ```
   *(Pour les configurations légères avec 8 Go de RAM, vous pouvez utiliser `ollama pull llama3.2:1b` et régler `OLLAMA_MODEL=llama3.2:1b`).*
4. Vérifier qu'Ollama fonctionne :
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Option B : Serveur local de développement (Inclus dans le dépôt)
Si le téléchargement d'Ollama est en cours ou indisponible, un serveur compatible avec l'API Ollama est inclus dans le projet :
```bash
python scripts/local_ollama_server.py
```
Il écoute sur `0.0.0.0:11434` et répond avec les spécifications complètes de `/api/tags` et `/api/chat`.

---

## 5. Fonctionnalités et Paramètres Supportés

### Actions IA :
- **Générer une publication** (`GENERATE`) : à partir d'un sujet, d'une consigne ou d'une idée brute.
- **Réécrire** (`REWRITE`) : reformulation complète.
- **Améliorer** (`IMPROVE`) : renforcement de l'impact, clarté et rythme.
- **Raccourcir** (`SHORTEN`) : synthèse percutante.
- **Développer** (`EXPAND`) : approfondissement structuré.
- **Changer de ton** (`CHANGE_TONE`) : bascule instantanée vers un autre style.
- **Adapter au réseau social** (`ADAPT_PLATFORM`) : mise en forme LinkedIn, Instagram ou Facebook.
- **Brainstormer des idées** (`IDEATE`) : génération d'angles et sujets de publications.

### Paramètres de personnalisation :
- **Réseau social** : LinkedIn (accroche, interlignes, takeaways, 2-4 hashtags), Instagram (storytelling, emojis soignés, CTA, 5-8 hashtags), Facebook (ton communautaire, débat, 1-3 hashtags).
- **Tonalités** : Professionnel, Amical & Chaleureux, Humoristique & Décalé, Commercial & Promotionnel, Décontracté, Formel, Technique.
- **Langue** : Français (`fr`), Anglais (`en`), Espagnol (`es`), Allemand (`de`).
- **Longueur** : Court (1-3 phrases), Moyen (1-2 paragraphes), Long (détaillé et structuré).
- **Options activables** :
  - Hashtags pertinents (`include_hashtags: true/false`)
  - Appel à l'action / CTA (`include_cta: true/false`)
  - Charte éditoriale de la marque (injectée dans le prompt système)

---

## 6. Interface Utilisateur (Frontend)

- **Badge de statut du fournisseur en temps réel** : Indique si Ollama est en ligne (pastille verte) ou indisponible (pastille ambre avec instructions de démarrage).
- **Bouton d'actualisation** : Permet de re-tester la connectivité d'Ollama sans recharger la page.
- **Édition directe in-place** : Le texte généré s'affiche dans une zone éditable avec compteur de caractères, mots et tokens.
- **Enregistrer en brouillon** : Envoie directement le contenu finalisé vers l'éditeur de publication (`/posts/new`).

---

## 7. Tests et Validation

Pour lancer la suite de tests IA :
```bash
docker exec communityai-backend pytest /app/tests/test_ai_ollama.py /app/tests/test_ai.py -v
```

Pour lancer la suite complète de 162 tests :
```bash
docker exec communityai-backend pytest /app/tests/ -q
```
