# CommunityAI Platform

CommunityAI is an AI-assisted community management platform for planning, publishing, monitoring, and responding to social activity from one workspace. It is an MVP built for a Master's internship project.

## Objectives

- Centralize community-management workflows.
- Keep a human in the loop for AI-generated content and replies.
- Provide provider integrations behind a backend security boundary.
- Make analytics, notifications, and reporting available from the same workspace.

## Features

- Email/password authentication, JWT access tokens, refresh-token revocation, and role-based access.
- True workspace data isolation and team collaboration: roles (Owner, Admin, Community Manager, Client), cryptographic invitations lifecycle, and audit logs.
- User profile, workspace settings, notification preferences, timezone, language, and password changes.
- Meta and LinkedIn social-account flows, encrypted backend token storage, and demo/mock mode.
- Drafts, scheduling, publishing, cancellation, and editorial calendar workflows.
- AI generation, rewriting, improvement, shortening, expansion, tone changes, platform adaptation, and ideas.
- Unified inbox with search, filters, read/resolved state, AI suggestions, and manual replies.
- Analytics KPIs, timeseries, top posts, mock seed data, CSV/PDF reporting, and notifications.


## Architecture and Stack

- Frontend: React, TypeScript, Vite, React Router, TanStack Query.
- Backend: FastAPI, Pydantic Settings, SQLAlchemy, Alembic.
- Data: PostgreSQL and Redis.
- Runtime: Docker Compose.
- AI: backend provider abstraction with mock, OpenAI, and Gemini configuration paths.
- Social: backend-owned Meta and LinkedIn OAuth/provider adapters.

The active frontend is [frontend/communityai](frontend/communityai). The root [communityai](communityai) directory is a legacy duplicate and is not used by Docker Compose.

## Repository Structure

```text
backend/                 FastAPI application, services, models, migrations, tests
frontend/communityai/    Canonical React/Vite application
communityai/             Legacy frontend duplicate, not the active app
docs/                    OAuth setup, manual QA, demo, and defense documentation
docker-compose.yml       PostgreSQL, Redis, backend, and frontend services
.env.example             Safe environment template with placeholders only
```

## Prerequisites

- Docker Desktop with Compose.
- Python 3.11+ for local backend commands.
- Node.js and npm for local frontend commands.
- Provider developer applications only when testing real Meta or LinkedIn OAuth.

## Environment Variables

Copy the template and edit the local file only:

```powershell
Copy-Item .env.example .env
```

The template documents PostgreSQL, CORS, JWT, cookie, OAuth, encryption, AI, Redis, and frontend URL variables. Never commit `.env` or paste its values into chat, tickets, screenshots, frontend code, or logs.

Generate the Fernet key used to encrypt social tokens:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the generated value in `SOCIAL_TOKEN_ENCRYPTION_KEY`. The backend rejects missing or invalid keys at startup and never generates a replacement automatically.

## Local Docker Installation

```powershell
Copy-Item .env.example .env
docker compose up -d --build
docker compose ps
```

The backend startup command runs `python -m alembic upgrade head` before Uvicorn. A fresh database therefore does not require a separate manual migration step. The expected migration head is `0008_create_user_settings`.

Stop the stack with:

```powershell
docker compose down
```

## Accessing the Application

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/health
- Swagger/OpenAPI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Local Development Without Docker

```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```powershell
cd frontend/communityai
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Local manual backend development still requires PostgreSQL, Redis, and the environment variables from `.env`.

## Social OAuth

For a presentation without external provider setup, set `SOCIAL_MOCK_MODE=true`. The UI then marks connections as demonstrations and uses mock accounts. Mock mode is not a real provider login.

For real OAuth, set `SOCIAL_MOCK_MODE=false`, generate a valid Fernet key, and configure real credentials from Meta for Developers and LinkedIn Developers. Register these exact callback URLs:

```text
http://localhost:8000/api/v1/social-accounts/meta/callback
http://localhost:8000/api/v1/social-accounts/linkedin/callback
```

Meta requires a configured application, Facebook Login/API access, and eligible Page/Instagram Professional permissions. LinkedIn requires an application with the Auth redirect URL, OpenID Connect for `openid profile email`, and Share on LinkedIn access if `w_member_social` is needed. See [docs/social-oauth-setup.md](docs/social-oauth-setup.md) and [docs/manual-social-oauth-test.md](docs/manual-social-oauth-test.md).

Real Meta/LinkedIn authorization and callbacks are external setup concerns and must not be described as verified while placeholder credentials are present.

## AI Configuration

Use `AI_PROVIDER=mock` for a deterministic demonstration. For a real provider, configure its backend-only API key and model variables in `.env`. Keys are never intentionally sent to the frontend. AI suggestions require human review before sending.

## Testing and Build

Backend tests:

```powershell
cd backend
python -m pytest -q
```

Frontend production build:

```powershell
cd frontend/communityai
npm run build
```

Deployment checks:

```powershell
docker compose config

cd backend
python -m alembic heads
```

The final QA checklist is [docs/FINAL_QA_CHECKLIST.md](docs/FINAL_QA_CHECKLIST.md).

## Known Limitations and Deployment Considerations

- MFA, WebAuthn, SSO, billing, and additional social networks are outside this MVP.
- Real social provider access depends on external app review, products, permissions, Page ownership, and developer-console redirect configuration.
- Local Compose defaults are for development; use strong JWT/database credentials, HTTPS, secure cookies, restricted CORS origins, managed PostgreSQL/Redis, and external secret management for deployment.
- The frontend uses an in-memory access token and an HttpOnly refresh cookie; review the session model against the target deployment threat model.
- Docker Compose provides local orchestration, not production HA, backup, ingress, or observability.

## Troubleshooting

- Backend will not start: inspect logs for an invalid `SOCIAL_TOKEN_ENCRYPTION_KEY`; generate a new valid Fernet key and restart.
- OAuth reports not configured: verify client ID, client secret, redirect URI, and `SOCIAL_MOCK_MODE` inside the running backend container, using booleans only.
- Provider rejects a redirect: compare the exact URI in `.env` with the provider console, including scheme, port, path, and trailing slash.
- Missing tables: run `docker compose up -d --build`; migrations run automatically before the backend starts.
- Frontend cannot call the API: verify `VITE_API_URL`/`BACKEND_CORS_ORIGINS` and that port `8000` is reachable.

## Current Implementation Status

The implemented MVP modules are present and covered by backend tests and frontend build validation. Docker startup, automatic migrations, safe OAuth status, encrypted token handling, and sanitized AI errors are implemented. Real Meta and LinkedIn provider authorization is not considered verified until genuine external credentials complete the authorization and callback flows.
