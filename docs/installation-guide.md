# CommunityAI - Guide d'Installation et de Déploiement

Ce guide détaille pas à pas la procédure d'installation, de configuration et d'exécution de la plateforme **CommunityAI**, en environnement conteneurisé Docker ou en développement local direct.

---

## 1. Prérequis Système

| Composant | Version Minimale | Rôle |
|---|---|---|
| **Système d'Exploitation** | Windows 10/11, macOS, Linux (Ubuntu 22.04+) | Système hôte |
| **Python** | 3.11 ou supérieur (3.11, 3.12, 3.13, 3.14) | Environnement backend |
| **Node.js** | 18.x ou 20.x LTS | Environnement frontend |
| **npm** | 9.x ou 10.x | Gestionnaire de dépendances frontend |
| **Docker & Compose** | Docker Desktop 4.x / Docker Engine 24+ | Conteneurisation (optionnelle en local) |
| **Ollama** | 0.3.x ou supérieur | Serveur d'inférence LLM local souverain |

---

## 2. Configuration des Variables d'Environnement

Dans la racine du projet `C:\projets\stage\communityai-platform` :

1. Copier le fichier d'exemple sécurisé :
   ```powershell
   Copy-Item .env.example .env
   ```

2. Générer la clé de chiffrement Fernet obligatoire pour sécuriser les tokens sociaux :
   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. Éditer `.env` et reporter la clé générée dans la variable `SOCIAL_TOKEN_ENCRYPTION_KEY` :
   ```ini
   SOCIAL_TOKEN_ENCRYPTION_KEY=votre_cle_fernet_generée_ici==
   ```

4. Configuration par défaut recommandée pour l'IA (Ollama local) :
   ```ini
   AI_PROVIDER=ollama
   OLLAMA_BASE_URL=http://127.0.0.1:11434
   OLLAMA_MODEL=smollm2:135m
   # Pour la production ou un modèle plus puissant :
   # OLLAMA_MODEL=llama3.2:3b
   ```

> [!CAUTION]
> Ne commitez jamais le fichier `.env` dans Git. Il est référencé dans le `.gitignore`.

---

## 3. Installation et Configuration d'Ollama (IA Locale)

1. **Télécharger et installer Ollama** depuis le site officiel : https://ollama.com/download.
2. **Démarrer le serveur Ollama** :
   ```powershell
   ollama serve
   ```
3. **Télécharger le modèle de travail** :
   ```powershell
   # Modèle ultra-léger pour tests rapides et démonstrations locales :
   ollama pull smollm2:135m

   # OU Modèle haute qualité recommandé pour production :
   ollama pull llama3.2:3b
   ```
4. **Vérifier l'accessibilité de l'API Ollama** :
   ```powershell
   curl http://127.0.0.1:11434/api/tags
   ```

---

## 4. Déploiement Local sans Docker (Mode Recommandé pour Débogage)

### 4.1. Lancement du Backend FastAPI

1. Ouvrir un premier terminal et se placer dans le sous-dossier `backend` :
   ```powershell
   cd c:\projets\stage\communityai-platform\backend
   ```
2. Créer et activer un environnement virtuel (optionnel mais conseillé) :
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Installer les dépendances Python :
   ```powershell
   pip install -r requirements.txt
   pip install python-multipart
   ```
4. Exécuter les migrations de base de données :
   ```powershell
   python -m alembic upgrade head
   ```
5. Démarrer le serveur API Uvicorn :
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

- Documentation interactive Swagger : http://localhost:8000/docs
- Point de santé de l'API : http://localhost:8000/health

---

### 4.2. Lancement du Frontend React / Vite

1. Ouvrir un second terminal et se placer dans le sous-dossier `frontend/communityai` :
   ```powershell
   cd c:\projets\stage\communityai-platform\frontend\communityai
   ```
2. Installer les paquets npm :
   ```powershell
   npm install
   ```
3. Démarrer le serveur de développement Vite :
   ```powershell
   npm run dev
   ```
4. Ouvrir l'application dans le navigateur : **http://localhost:5173**

---

## 5. Déploiement via Docker Compose

Pour déployer l'intégralité de la stack (PostgreSQL, Redis, Backend, Frontend) dans des conteneurs isolés :

1. Lancer Docker Desktop sur votre machine.
2. Dans la racine du dépôt :
   ```powershell
   docker compose up -d --build
   ```
3. Vérifier le statut des conteneurs :
   ```powershell
   docker compose ps
   ```
4. Pour consulter les logs du backend :
   ```powershell
   docker compose logs -f backend
   ```
5. Arrêter les services :
   ```powershell
   docker compose down
   ```

> [!NOTE]
> Dans Docker Compose, le backend accède au serveur Ollama de la machine hôte via `http://host.docker.internal:11434`.

---

## 6. Exécution des Tests et Vérifications de Conformité

### 6.1. Suite Complète des Tests Backend (Pytest)
```powershell
cd c:\projets\stage\communityai-platform
python -m pytest
```
*Résultat attendu : 177 tests passés avec succès.*

### 6.2. Script d'Audit E2E du Module AI Community Manager
```powershell
python backend/scripts/audit_ai_community_manager.py
```
*Résultat attendu : 10/10 tests critiques validés (Multi-tenancy, Grounding, Ollama réel, Anti-injection, Sécurité Mode 3, Webhooks).*

### 6.3. Scénarios Académiques de Soutenance (Boulangerie Étoile)
```powershell
python backend/scripts/test_demo_scenarios.py
```
*Résultat attendu : 4/4 scénarios validés (Prix factuel, Inconnu escaladé, Réclamation bloquée, Injection neutralisée).*

### 6.4. Vérification Frontend (Lint & Build)
```powershell
cd frontend/communityai
npm run lint
npm run build
```
*Résultat attendu : 0 erreur de linting, build TypeScript/Vite généré avec succès dans `dist/`.*

