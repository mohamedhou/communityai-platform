# Manual Social OAuth Test

This checklist validates the real provider flow. It requires provider developer applications and credentials configured outside the repository.

## Before Testing

1. Copy `.env.example` to `.env`.
2. Generate and set `SOCIAL_TOKEN_ENCRYPTION_KEY`.
3. Set `SOCIAL_MOCK_MODE=false`.
4. Configure the exact provider redirect URIs:
   - Meta: `http://localhost:8000/api/v1/social-accounts/meta/callback`
   - LinkedIn: `http://localhost:8000/api/v1/social-accounts/linkedin/callback`
5. Start the stack:

```powershell
docker compose up -d --build
```

6. Open `http://localhost:5173/login`, authenticate, then open `/social-accounts`.
7. In DevTools, keep Console and Network open. Never copy tokens or secrets into logs or tickets.

## Meta

1. Set `META_CLIENT_ID`.
2. Set `META_CLIENT_SECRET`.
3. Set `META_REDIRECT_URI` to the exact local URI.
4. Set a currently supported `META_GRAPH_API_VERSION`.
5. Click **Connect Meta**.
6. Confirm the browser leaves localhost and opens the Meta authorization host.
7. Log in and authorize the application.
8. Confirm the browser returns to `http://localhost:5173/social-accounts`.
9. Confirm the connected Facebook Page appears.
10. Confirm an eligible Instagram Professional account appears when it is linked to an authorized Page and the Meta app has the required access.
11. Confirm no access token, client secret, or encrypted credential appears in the page, response JSON, or logs.

Expected initiation request:

- `GET http://localhost:8000/api/v1/social-accounts/meta/connect`
- HTTP `200`
- JSON response containing `url`
- Browser navigation to the returned Meta authorization URL

## LinkedIn

1. Set `LINKEDIN_CLIENT_ID`.
2. Set `LINKEDIN_CLIENT_SECRET`.
3. Set `LINKEDIN_REDIRECT_URI` to the exact local URI.
4. Confirm OpenID Connect is available for the LinkedIn application.
5. Enable Share on LinkedIn if posting is required.
6. Click **Connect LinkedIn**.
7. Confirm the browser opens LinkedIn authorization.
8. Log in and authorize the application.
9. Confirm the browser returns to `http://localhost:5173/social-accounts`.
10. Confirm the LinkedIn identity appears.
11. Confirm no access token, client secret, or encrypted credential appears in the page, response JSON, or logs.

Expected initiation request:

- `GET http://localhost:8000/api/v1/social-accounts/linkedin/connect`
- HTTP `200`
- JSON response containing `url`
- Browser navigation to the returned LinkedIn authorization URL

## Configuration Failure Test

1. Temporarily remove one provider's client ID or secret from `.env`.
2. Restart the backend.
3. Click that provider's connect button.
4. Confirm the UI displays a safe configuration error such as `Meta OAuth is not configured` or `LinkedIn OAuth is not configured`.
5. Confirm no secret, stack trace, or token is displayed.

## Mock Mode Regression Test

1. Set `SOCIAL_MOCK_MODE=true`.
2. Restart the stack.
3. Open `/social-accounts`.
4. Confirm the page displays **Mode démonstration activé**.
5. Confirm buttons are labelled as demo connections.
6. Click a demo button and confirm the page reports a demonstration connection, not a real provider connection.
