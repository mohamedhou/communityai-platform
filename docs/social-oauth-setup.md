# Social OAuth Setup

CommunityAI supports Meta (Facebook Pages and eligible Instagram Professional accounts) and LinkedIn OAuth. The backend owns the OAuth flow and encrypts provider tokens before persistence. React never receives provider tokens or client secrets.

## Local Environment

Copy the repository `.env.example` to `.env` and fill values locally. Never commit `.env` or paste secrets into frontend files.

```env
SOCIAL_MOCK_MODE=false
SOCIAL_TOKEN_ENCRYPTION_KEY=<generate-a-fernet-key>
META_CLIENT_ID=
META_CLIENT_SECRET=
META_REDIRECT_URI=http://localhost:8000/api/v1/social-accounts/meta/callback
META_GRAPH_API_VERSION=v24.0
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/v1/social-accounts/linkedin/callback
FRONTEND_APP_URL=http://localhost:5173
```

Generate a Fernet key with the backend environment, for example:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The exact redirect URIs must match all three places: `.env`, the authorization request, and the provider developer portal. Do not add a trailing slash or change the protocol, host, port, or path.

## Meta Developer Setup

1. Create or sign in to [Meta for Developers](https://developers.facebook.com/).
2. Create a Meta application and record its App ID and App Secret.
3. Add and configure the Meta products and permissions required by the current Page and Instagram Graph API access in the Meta dashboard. Availability depends on the app mode, app review, business assets, and the account being connected.
4. Configure the app's OAuth redirect settings.
5. Register this exact redirect URI:

   `http://localhost:8000/api/v1/social-accounts/meta/callback`

6. Put the App ID in `META_CLIENT_ID` and the App Secret in `META_CLIENT_SECRET`, only in the local `.env`.
7. Set `META_GRAPH_API_VERSION` to a currently supported Graph API version for the products enabled in the Meta dashboard. The application sends this value to the authorization, token, Page, and Instagram Graph endpoints.
8. Ensure the user can access the Facebook Page. The implementation requests authorized Pages and checks each Page for an eligible `instagram_business_account`.
9. Ensure the Instagram account is a Professional account connected to an eligible Facebook Page. Meta controls final eligibility and permissions.
10. Set `SOCIAL_MOCK_MODE=false` and restart the backend.

The application uses the current configured Graph API version and stores only Page/Instagram metadata plus encrypted provider credentials. Meta developer products and permissions can change; follow the current Meta documentation for the exact dashboard labels and review requirements.

## LinkedIn Developer Setup

1. Create or sign in to [LinkedIn Developers](https://www.linkedin.com/developers/).
2. Create an application and open its **Auth** configuration.
3. Add this exact Authorized Redirect URL:

   `http://localhost:8000/api/v1/social-accounts/linkedin/callback`

4. Enable the LinkedIn products required by the capabilities you use. OpenID Connect must be available for member identity. Enable **Share on LinkedIn** if posting requires `w_member_social`.
5. Copy the application Client ID to `LINKEDIN_CLIENT_ID` and Client Secret to `LINKEDIN_CLIENT_SECRET`, only in the local `.env`.
6. CommunityAI requests these scopes:

   `openid profile email w_member_social`

   The final set available to an application depends on the products and permissions approved in the LinkedIn Developer Portal.
7. Set `LINKEDIN_REDIRECT_URI` to the exact URI above.
8. Set `SOCIAL_MOCK_MODE=false` and restart the backend.

The current implementation uses LinkedIn OAuth 2.0 authorization code flow, the access-token endpoint, and the OpenID Connect `userinfo` endpoint. LinkedIn product access and API permissions are controlled by LinkedIn and cannot be bypassed by the application.

## Safe Configuration Check

With an authenticated browser session, request:

`GET /api/v1/social-accounts/config-status`

The response contains only booleans and mode information:

```json
{
  "mock_mode": false,
  "meta_configured": true,
  "linkedin_configured": true
}
```

It never returns client IDs, client secrets, tokens, or encryption keys.

## Application Endpoints

- `GET /api/v1/social-accounts/meta/connect` returns `{ "url": "..." }` and the browser navigates to that URL.
- `GET /api/v1/social-accounts/linkedin/connect` returns `{ "url": "..." }` and the browser navigates to that URL.
- `GET /api/v1/social-accounts/meta/callback` handles the Meta callback.
- `GET /api/v1/social-accounts/linkedin/callback` handles the LinkedIn callback.
- `DELETE /api/v1/social-accounts/{account_id}` disconnects an owned account.
- `POST /api/v1/social-accounts/{account_id}/refresh` reconnects supported accounts using stored encrypted credentials.

OAuth state is random, provider-bound, expiring, single-use, and consumed with the account upsert. Callback errors are sanitized before redirecting back to `/social-accounts`.

## Mock Mode

For local demos only, set `SOCIAL_MOCK_MODE=true`. The UI displays **Mode démonstration activé**, labels the buttons as demo connections, and names the success as demonstration mode. Mock accounts are not real provider connections.

For real OAuth, set `SOCIAL_MOCK_MODE=false`, configure both provider applications as needed, and restart Docker.

## Troubleshooting

1. Confirm the provider portal URI exactly matches the `.env` URI.
2. Confirm Docker receives the variables with `docker compose config`; inspect only booleans or empty/non-empty status, never secret values.
3. Open browser DevTools and confirm the connect request returns `200` with a JSON `url`.
4. Confirm the browser leaves `localhost` for the provider authorization host.
5. If credentials are missing, the UI/API reports that the provider OAuth is not configured.
6. If the provider rejects a scope or product, enable the required product or permission in the provider portal; do not add deprecated scopes blindly.
