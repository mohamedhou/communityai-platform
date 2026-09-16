# CommunityAI Platform

CommunityAI is an AI-assisted community management platform built as a realistic MVP for a two-month internship.

## Current scope

Implemented now:

- Project foundation (FastAPI + React + PostgreSQL + Redis + Docker Compose)
- Authentication with email/password
- JWT access token
- Refresh token flow with server-side revocation
- Protected route `/api/v1/auth/me`
- Basic RBAC checks
- Social account connections for Meta and LinkedIn, including mock mode
- Post drafts, scheduling, publishing, and calendar workflows
- AI assistant actions with mock and configurable provider support
- Unified inbox with AI reply suggestions and manual replies
- Analytics, reporting exports, notifications, and user settings

Out of scope for this MVP:

- MFA, WebAuthn, SSO
- Additional social providers such as Google and Microsoft

## Canonical frontend

Canonical frontend path is [frontend/communityai](frontend/communityai).

The root [communityai](communityai) folder is kept temporarily as an old duplicate and is not used as the active frontend.

## Architecture

- Frontend: [frontend/communityai](frontend/communityai)
- Backend: [backend](backend)
- Database: PostgreSQL
- Cache: Redis
- Orchestration: Docker Compose

## Environment configuration

Create `.env` at repository root from [.env.example](.env.example).

Core variables:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `BACKEND_CORS_ORIGINS`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `REFRESH_COOKIE_NAME`
- `REFRESH_COOKIE_SECURE`
- `REFRESH_COOKIE_SAMESITE`
- `REFRESH_COOKIE_PATH`
- `SOCIAL_MOCK_MODE`
- `SOCIAL_TOKEN_ENCRYPTION_KEY`
- `META_CLIENT_ID`, `META_CLIENT_SECRET`, `META_REDIRECT_URI`
- `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REDIRECT_URI`
- `FRONTEND_APP_URL`

Never commit a real `.env` file.

Generate a valid Fernet encryption key locally with:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Place the generated value in local `.env` as `SOCIAL_TOKEN_ENCRYPTION_KEY`.

## Authentication strategy

- Access token: short lifetime JWT used for API authorization.
- Refresh token: longer lifetime JWT stored in `HttpOnly` cookie.
- Backend stores only a SHA-256 hash of refresh tokens in database.
- Logout flow revokes refresh token server-side and clears cookie.
- After logout, old refresh token cannot issue a new access token.

Current frontend compromise for MVP:

- Access token is kept in in-memory React state (not persisted in localStorage).
- Refresh token is primarily handled through cookie-based flow.

## API endpoints

Auth routes under `/api/v1/auth`:

- `POST /register`
- `POST /login`
- `POST /refresh`
- `GET /me`
- `POST /logout`
- `GET /admin-check` (RBAC validation endpoint)

## Install and run

Backend dependencies:

```powershell
cd backend
pip install -r requirements.txt
```

Frontend dependencies:

```powershell
cd frontend/communityai
npm install
```

Docker Compose:

```powershell
docker compose up --build
```

The backend applies pending Alembic migrations before starting the API.

OAuth setup, mock mode, and the manual provider checklist are documented in
[docs/social-oauth-setup.md](docs/social-oauth-setup.md) and
[docs/manual-social-oauth-test.md](docs/manual-social-oauth-test.md).

Manual backend:

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Manual frontend:

```powershell
cd frontend/communityai
npm run dev -- --host 0.0.0.0 --port 5173
```

## Useful URLs

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Validation commands

```powershell
python -m compileall backend/app
cd backend; pytest
cd ../frontend/communityai; npm run build
cd ../..; docker compose config
cd backend; python -m alembic heads
```
