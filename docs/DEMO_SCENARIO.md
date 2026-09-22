# CommunityAI Demo Scenario

Target duration: 10 to 15 minutes. The presenter should use a prepared local Docker stack and a demo account. Use `SOCIAL_MOCK_MODE=true` when real provider applications are unavailable.

## 1. Introduction

**Presenter does:** Introduce CommunityAI as an AI-assisted community-management workspace.

**Audience sees:** The running application and the main workspace navigation.

**Demonstrates:** The platform connects content planning, social activity, AI assistance, analytics, notifications, and reporting.

**Expected result:** The audience understands the product problem and the integrated MVP scope.

**Fallback:** Explain that mock mode is intentional for repeatable demonstrations; it does not represent a real provider login.

## 2. Login

**Presenter does:** Open `/login` and sign in with the prepared demo account.

**Audience sees:** Successful authentication and the dashboard.

**Demonstrates:** Email/password login, access-token handling, refresh-cookie session, and protected routing.

**Expected result:** The user reaches the authenticated workspace.

**Fallback:** Use the already authenticated browser tab and explain that authentication has been covered by automated tests.

## 3. Dashboard / Workspace

**Presenter does:** Show the dashboard cards and navigation briefly.

**Audience sees:** Workspace summary, account context, and navigation to the product modules.

**Demonstrates:** The application shell and cross-module entry points.

**Expected result:** The audience can see where content, inbox, analytics, and settings fit together.

**Fallback:** Navigate directly to the next module if demo data makes a dashboard card empty.

## 4. Social Accounts

**Presenter does:** Open `/social-accounts` and show connected demo accounts.

**Audience sees:** Meta/LinkedIn integration cards, connected channels, and mock-mode status when enabled.

**Demonstrates:** Provider abstraction, account ownership, safe configuration status, and the distinction between demo and real OAuth.

**Expected result:** Demo accounts appear without exposing tokens.

**Fallback:** State clearly that real Meta and LinkedIn authorization requires valid external developer applications, credentials, products, permissions, and exact callback URLs.

## 5. Create Content

**Presenter does:** Open Posts, create content for a connected demo account, and save it as a draft.

**Audience sees:** A new post in `DRAFT` state.

**Demonstrates:** Content creation, social-account ownership, validation, and persistence.

**Expected result:** The draft is visible in the posts list.

**Fallback:** Use an existing prepared draft if time is limited.

## 6. AI-Assisted Content Generation

**Presenter does:** Open the AI Assistant and generate or improve copy, then edit the result manually.

**Audience sees:** Generated content and the editable human-approved text.

**Demonstrates:** Provider abstraction, mock AI behavior, multiple writing actions, and human-in-the-loop review.

**Expected result:** The presenter keeps control of the final content before saving or publishing.

**Fallback:** Use mock AI mode and explain that real provider keys remain backend-only.

## 7. Editorial Calendar

**Presenter does:** Schedule the draft for a future time, open Calendar, and reschedule it.

**Audience sees:** The post in the calendar at the selected date/time.

**Demonstrates:** Scheduling, UTC normalization, calendar views, filters, and rescheduling.

**Expected result:** The post moves to its new date and remains associated with the account.

**Fallback:** Use the prepared scheduled post if drag-and-drop is unreliable in the presentation environment.

## 8. Unified Inbox

**Presenter does:** Open Inbox and seed or display a mock interaction.

**Audience sees:** A comment/message/mention with unread and resolved state.

**Demonstrates:** Unified interaction list, filters, search, ownership, and notification integration.

**Expected result:** The interaction opens and can be marked read or resolved.

**Fallback:** Seed mock interactions only when `SOCIAL_MOCK_MODE=true`.

## 9. AI Reply Suggestion

**Presenter does:** Request a reply suggestion, edit it, and send it manually.

**Audience sees:** Suggested text first, then the edited reply action.

**Demonstrates:** AI assistance without automatic sending and provider dispatch behind the backend.

**Expected result:** The suggestion is never sent until the presenter explicitly confirms the manual reply.

**Fallback:** Show the suggestion and stop before sending if no real/mock social account is available.

## 10. Analytics

**Presenter does:** Open Analytics, apply a date/platform filter, and show KPIs, timeseries, and top posts.

**Audience sees:** Followers, growth, reach, impressions, engagement, engagement rate, and charts.

**Demonstrates:** Snapshot-based aggregation, filters, zero-division protection, and account ownership.

**Expected result:** Values update consistently with the selected period and account.

**Fallback:** Seed mock analytics data before the defense.

## 11. Notifications

**Presenter does:** Open the notification center and show a notification produced by scheduling, publishing, or inbox activity.

**Audience sees:** Unread badge, list item, and read/delete controls.

**Demonstrates:** Cross-module event feedback and unread state management.

**Expected result:** Marking a notification read updates the counter.

**Fallback:** Use prepared notifications if the live action was already completed.

## 12. Settings / Workspace

**Presenter does:** Open Settings and show profile, workspace, timezone, language, and notification preferences.

**Audience sees:** Persisted user and workspace configuration.

**Demonstrates:** Personalization and secure password-change workflow.

**Expected result:** A safe non-sensitive preference change persists.

**Fallback:** Do not change the demo password during the defense; use the settings screen for read-only presentation.

## 13. Reporting / Export

**Presenter does:** Open Reports, select a period, preview the report, and export CSV and PDF.

**Audience sees:** KPI parity with Analytics, timeseries, top posts, and downloadable files.

**Demonstrates:** Reuse of analytics calculations and export workflows without secret exposure.

**Expected result:** CSV is UTF-8 compatible and PDF is readable.

**Fallback:** Prepare one previously generated export for inspection if the browser download dialog interrupts the flow.

## 14. Final Conclusion

**Presenter does:** Summarize the integrated workflow from authentication to reporting.

**Audience sees:** A coherent platform rather than isolated screens.

**Demonstrates:** The MVP's value: assisted content operations, controlled AI, unified community interactions, measurable outcomes, and exportable reporting.

**Expected result:** The audience understands what is implemented, what is simulated in mock mode, and what remains external provider setup.

**Fallback:** If Meta or LinkedIn is unavailable, state: the OAuth code, state validation, encryption, safe errors, and mock path are implemented; provider authorization requires valid developer-console credentials and was not claimed as manually verified.
