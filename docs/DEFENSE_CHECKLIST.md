# CommunityAI Defense Checklist

Prepare this checklist before the Master's internship defense.

## Application and Infrastructure

- [ ] Application launched before the defense
- [ ] `docker compose ps` checked
- [ ] Backend container running
- [ ] Frontend container running
- [ ] PostgreSQL healthy
- [ ] Redis healthy
- [ ] `/health` returns `200`
- [ ] Swagger/OpenAPI tab prepared at `http://localhost:8000/docs`
- [ ] Database migrated to `0008_create_user_settings`

## Quality Evidence

- [ ] Backend test suite passed
- [ ] Frontend production build passed
- [ ] `docker compose config` passed
- [ ] `git diff --check` passed
- [ ] `.env` is not tracked
- [ ] No secrets appear in screenshots, logs, slides, or recordings

## Demo Account and Data

- [ ] Demo account can log in
- [ ] Demo account role is known
- [ ] Demo social accounts/data are prepared
- [ ] At least one draft post is prepared
- [ ] At least one scheduled post is prepared
- [ ] Calendar data is visible
- [ ] Mock inbox interaction is prepared if needed
- [ ] Analytics snapshots are seeded if needed
- [ ] Notifications are prepared
- [ ] One report preview is ready
- [ ] CSV export path is known
- [ ] PDF export path is known

## Configuration

- [ ] `SOCIAL_MOCK_MODE` decision made before the defense
- [ ] If mock mode is used, the demo banner is understood and explained
- [ ] AI provider mode is prepared
- [ ] Fernet key is valid
- [ ] Real Meta/LinkedIn credentials are not shown in the presentation
- [ ] OAuth limitation explanation is prepared

## Browser and Presentation

- [ ] Browser tabs prepared: app, Swagger, optionally provider documentation
- [ ] Browser zoom and window size tested
- [ ] Console is clear of avoidable errors
- [ ] Network tab is closed or filtered before screen sharing
- [ ] Download folder is ready for CSV/PDF demonstration
- [ ] Presenter has the [demo scenario](DEMO_SCENARIO.md) open or printed

## Fallback Plan

- [ ] If external APIs are unavailable, switch to `SOCIAL_MOCK_MODE=true`
- [ ] Use seeded demo accounts and analytics
- [ ] Use mock AI provider
- [ ] Explain that mock mode demonstrates application behavior, not provider authorization
- [ ] Explain that real Meta/LinkedIn login requires external developer applications, approved products/permissions, valid credentials, and exact redirect URLs
- [ ] Do not claim real OAuth callback success unless it was completed before the defense
- [ ] Keep a screenshot or prepared export only as a fallback, never as a substitute for explaining the live workflow
