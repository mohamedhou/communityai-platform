# CommunityAI Final QA Checklist

Use this checklist before a demonstration or deployment review. Mark each item with exactly one state: `[ ] not tested`, `[x] passed`, or `[!] blocked`.

## A. Infrastructure

- [ ] not tested Docker starts successfully with `docker compose up -d --build`
- [ ] not tested PostgreSQL is healthy
- [ ] not tested Redis is healthy
- [ ] not tested backend is reachable at `/health`
- [ ] not tested frontend is reachable at `http://localhost:5173`
- [ ] not tested migrations are applied automatically
- [ ] not tested Alembic head is `0008_create_user_settings`

## B. Authentication

- [ ] not tested Register and login
- [ ] not tested `/api/v1/auth/me`
- [ ] not tested Refresh token
- [ ] not tested Logout
- [ ] not tested Revoked refresh token is rejected
- [ ] not tested Invalid credentials
- [ ] not tested Protected routes reject unauthenticated requests
- [ ] not tested ADMIN, COMMUNITY_MANAGER, and CLIENT RBAC behavior

## C. Social Accounts

- [ ] not tested Account list and ownership
- [ ] not tested Meta connect endpoint
- [ ] not tested LinkedIn connect endpoint
- [ ] not tested OAuth state provider binding and expiry
- [ ] not tested OAuth callback success/error handling
- [ ] not tested Demo/mock banner and mock accounts
- [ ] not tested Real Meta credentials and provider authorization
- [ ] not tested Real LinkedIn credentials and provider authorization
- [ ] not tested Token encryption and non-exposure

Real provider authorization is blocked until genuine Meta and LinkedIn applications and credentials are configured.

## D. Publishing

- [ ] not tested Create draft
- [ ] not tested Schedule
- [ ] not tested Cancel
- [ ] not tested Publish/mock publish
- [ ] not tested Invalid state transitions
- [ ] not tested Provider failure moves post to `FAILED`
- [ ] not tested Notifications are generated

## E. Editorial Calendar

- [ ] not tested Month view
- [ ] not tested Week view
- [ ] not tested Filters
- [ ] not tested Drag and drop
- [ ] not tested Rescheduling
- [ ] not tested Rollback on failure
- [ ] not tested UTC/timezone behavior

## F. AI Assistant

- [ ] not tested Generation
- [ ] not tested Rewrite
- [ ] not tested Tone change
- [ ] not tested Platform adaptation
- [ ] not tested Ideas
- [ ] not tested Safe provider errors
- [ ] not tested Human approval before sending
- [ ] not tested Provider keys remain backend-only

## G. Unified Inbox

- [ ] not tested Comments/messages/mentions list
- [ ] not tested Search and filters
- [ ] not tested Mark read/unread
- [ ] not tested Resolve/unresolve
- [ ] not tested AI reply suggestion
- [ ] not tested Manual reply
- [ ] not tested AI suggestion never sends automatically

## H. Analytics

- [ ] not tested KPIs
- [ ] not tested Date filters
- [ ] not tested Platform filters
- [ ] not tested Social-account filters
- [ ] not tested Timeseries charts
- [ ] not tested Top posts
- [ ] not tested Latest follower snapshot aggregation
- [ ] not tested Follower growth formula
- [ ] not tested Engagement-rate formula
- [ ] not tested Zero-reach protection

## I. Notifications

- [ ] not tested Unread counter
- [ ] not tested Notification list
- [ ] not tested Mark read/unread
- [ ] not tested Mark all read
- [ ] not tested Delete
- [ ] not tested Navbar badge and dropdown

## J. Settings

- [ ] not tested Profile
- [ ] not tested Workspace settings
- [ ] not tested Notification preferences
- [ ] not tested Social settings
- [ ] not tested Timezone and language
- [ ] not tested Password change
- [ ] not tested Current password validation
- [ ] not tested Refresh-session revocation after password change

## K. Reporting

- [ ] not tested Report preview
- [ ] not tested Analytics KPI parity
- [ ] not tested CSV export
- [ ] not tested UTF-8/French characters
- [ ] not tested PDF export
- [ ] not tested PDF readability and absence of sensitive data

## L. Security

- [ ] not tested `.env` is ignored and untracked
- [ ] not tested No secrets in frontend assets
- [ ] not tested No access/refresh tokens in API responses
- [ ] not tested OAuth errors are provider-specific and sanitized
- [ ] not tested AI errors do not expose stack traces
- [ ] not tested Fernet key is structurally valid
- [ ] not tested CORS contains only intended origins
- [ ] not tested Cross-user resource isolation

## Final Commands

```powershell
cd backend
python -m pytest -q
cd ../frontend/communityai
npm run build
cd ../..
docker compose config
docker compose ps
cd backend
python -m alembic heads
cd ..
git diff --check
git ls-files .env
```
