# CommunityAI Platform

CommunityAI is an AI-assisted community management platform built as a realistic MVP for a two-month internship. The current setup is a clean foundation for the future features, not the full product.

## Current architecture

- Frontend: [frontend/communityai](frontend/communityai)
- Backend: [backend](backend)
- Database: PostgreSQL
- Cache: Redis
- Orchestration: Docker Compose

The duplicate [communityai](communityai) folder at the repository root is kept for now and is not used as the canonical frontend.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ for local backend runs
- Node.js 20+ for local frontend runs

## Environment

Create a local `.env` file at the repository root from [.env.example](.env.example).

Required variables:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `BACKEND_CORS_ORIGINS`

Never commit a real `.env` file.

## Installation

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

## Run with Docker Compose

From the repository root:

```powershell
docker compose up --build
```

Services:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Manual backend run

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Manual frontend run

```powershell
cd frontend/communityai
npm run dev -- --host 0.0.0.0 --port 5173
```

## Validation endpoints

- Root API: http://localhost:8000/
- Health: http://localhost:8000/health
- OpenAPI docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
# CommunityAI Platform

CommunityAI is an AI-powered Social Media Management Platform designed to help community managers centralize, automate, and optimize their daily workflows.

## Features

- Secure authentication (JWT + RBAC)
- Multi-account social media management
- Content publishing and editorial calendar
- AI-powered content generation
- Unified inbox
- Analytics dashboard
- Automated reporting

## Tech Stack

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query

### Backend
- FastAPI
- Python 3.11
- SQLAlchemy
- PostgreSQL
- Redis
- Celery

### AI
- OpenAI GPT-4o
- LangChain

### Infrastructure
- Docker
- Nginx
- MinIO

## Project Structure
