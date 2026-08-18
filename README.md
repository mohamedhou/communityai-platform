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

Not implemented yet:

- MFA, WebAuthn, SSO
- Social OAuth providers (Google, Microsoft, Meta, LinkedIn)
- Social publishing, calendar, inbox, analytics, AI assistant business features

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

Never commit a real `.env` file.

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
```
