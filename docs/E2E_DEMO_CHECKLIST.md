# CommunityAI E2E Demo Checklist

## Setup

1. Copy `.env.example` to `.env` and provide local development values only.
2. Start the stack with `docker compose up -d --build`.
3. Confirm PostgreSQL and Redis are healthy.
4. Confirm `http://localhost:8000/health` returns `200`.
5. Use `SOCIAL_MOCK_MODE=true` for local demonstrations without live provider credentials.

## Authentication

1. Register a demo user.
2. Confirm a default workspace is created.
3. Log in and confirm the protected application loads.
4. Open `/profile` and verify the current user.
5. Log out and confirm protected routes redirect to `/login`.
6. Confirm refresh fails after logout.

## Workspace

1. Open workspace members and invitations.
2. Invite a second user as `COMMUNITY_MANAGER` or `CLIENT`.
3. Accept the invitation with the invited account.
4. Confirm the active workspace context is preserved.
5. Keep a second workspace available for isolation checks.

## Social accounts

1. Enable mock mode for local testing.
2. Connect the mock Meta or LinkedIn account from Social Accounts.
3. Confirm the account appears in the active workspace.
4. Confirm the account is not visible from another workspace.
5. Live Meta/LinkedIn OAuth requires real credentials and is not covered by the local demo.

## Media

1. Open `/media`.
2. Upload a small PNG or JPEG.
3. Confirm progress, success state, preview, and library listing.
4. Select the asset from the post composer.
5. Replace and remove the selected asset.
6. Delete the asset from the library after detaching it from posts.
7. Restart the backend and confirm retained files remain available.

## Content

1. As a Community Manager, create a draft.
2. Select a shared social account and media asset.
3. Save the draft.
4. Confirm the draft remains editable and is not published automatically.

## AI

1. Generate or improve post content from the AI Assistant.
2. Copy the result into the composer.
3. Confirm AI actions do not publish, schedule, or alter approval status.
4. Confirm provider errors do not expose API keys.

## Approval

1. Submit the Community Manager draft for review.
2. Log in as the workspace Owner or Admin.
3. Open Review Queue and inspect content plus media.
4. Approve the post.
5. Confirm approval notification and audit activity.
6. As the Community Manager, schedule the approved post.
7. Confirm a `NOT_REQUIRED` Community Manager post cannot be scheduled or published.

## Calendar

1. Confirm the approved scheduled post appears in the calendar.
2. Confirm schedule changes preserve workspace and approval rules.
3. Edit an approved scheduled post and confirm it returns to `DRAFT`, clears `scheduled_at`, and requires resubmission.

## Publishing

1. Publish only an approved post as Community Manager.
2. Confirm Owner/Admin can publish `NOT_REQUIRED` content according to policy.
3. In mock mode, verify the provider response and resulting post state.
4. Do not claim external publication without real provider credentials.

## Inbox

1. Seed or load mock inbox data.
2. Verify unread count.
3. Mark a message read.
4. Resolve a message.
5. Generate an AI reply suggestion.
6. Send a manual reply.
7. Repeat from another workspace and confirm isolation.

## Analytics

1. Open Analytics.
2. Check KPI summary, timeseries, account filters, and top posts.
3. Confirm Workspace A data never appears in Workspace B.
4. Use mock seed data only for local demonstration.

## Reporting

1. Select a date range and optional account filter.
2. Generate the report preview.
3. Export CSV.
4. Export PDF.
5. Confirm report content is workspace-scoped.

## Notifications and audit

Verify notifications for:

- invitation and acceptance;
- post submission;
- approval;
- rejection;
- resubmission;
- member changes.

Verify `WorkspaceActivity` includes the workspace, actor, event, details, and timestamp. It is an append-only application audit log, not cryptographically tamper-evident.

## Known external limitations

- Local media content is authenticated and is not automatically publishable by Meta or LinkedIn.
- Live OAuth and live provider publication require real provider credentials and callback configuration.
- Local media storage uses the Docker `media_data` volume; production should use durable object storage.
