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

Official references: [Meta Login manual flow](https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow/), [Pages API getting started](https://developers.facebook.com/docs/pages-api/get-started), and [Instagram API getting started](https://developers.facebook.com/docs/instagram-api/getting-started).

1. Create or sign in to [Meta for Developers](https://developers.facebook.com/), open **My Apps**, and create an application. The exact creation flow and product names can vary by Meta dashboard version.
2. Open the application dashboard. The App ID shown in the app settings is the OAuth client ID; record it for `META_CLIENT_ID`. Reveal the App Secret from the app's basic settings and store it only as `META_CLIENT_SECRET` in the local `.env`.
3. Add the login product used by the app. In the application dashboard, open **Facebook Login > Settings**, then add the callback under **Client OAuth Settings > Valid OAuth Redirect URIs**. Register this exact redirect URI:

   `http://localhost:8000/api/v1/social-accounts/meta/callback`

4. Ensure the app has access to the Page and Instagram Graph API capabilities needed by this implementation. The authorization request asks for `pages_show_list`, `pages_read_engagement`, `instagram_basic`, and `instagram_manage_insights`; Meta may require products, permissions, business verification, App Review, or development-mode roles before these can be used outside the app's test roles.
5. Ensure the person authorizing the app has access to the target Facebook Page. The callback flow calls the Pages API, then checks each returned Page for an `instagram_business_account`.
6. For Instagram results, use an Instagram Professional account connected to an eligible Facebook Page. Personal Instagram accounts are not sufficient for this Page-linked Graph API flow. Meta controls the final eligibility and permission requirements.
7. Set `META_GRAPH_API_VERSION` to a currently supported Graph API version for the products enabled in the Meta dashboard. If it is blank, the application configuration default is used; keep the version aligned with Meta's supported Graph API versions.
8. Put the App ID and App Secret only in the local `.env`, set `SOCIAL_MOCK_MODE=false`, and restart Docker.

The application uses the current configured Graph API version and stores only Page/Instagram metadata plus encrypted provider credentials. Meta developer products and permissions can change; follow the current Meta documentation for the exact dashboard labels and review requirements.

## LinkedIn Developer Setup

Official references: [LinkedIn 3-legged OAuth](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow) and [Sign In with LinkedIn using OpenID Connect](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2).

1. Create or sign in to [LinkedIn Developers](https://www.linkedin.com/developers/), open **My apps**, and create an application.
2. In the application **Auth** tab, copy the displayed API key/Client ID to `LINKEDIN_CLIENT_ID`. Copy the Client Secret to `LINKEDIN_CLIENT_SECRET` and keep it only in the local `.env`.
3. In the same **Auth** tab, add this exact Authorized Redirect URL:

   `http://localhost:8000/api/v1/social-accounts/linkedin/callback`

4. In the **Products** tab, request or enable **Sign In with LinkedIn using OpenID Connect**. This provides the `openid`, `profile`, and `email` scopes and supports the application's `userinfo` lookup.
5. Enable or request **Share on LinkedIn** if posting is required. The `w_member_social` scope is available only when the corresponding product or partner access is provisioned for the application.
6. CommunityAI requests these scopes:

   `openid profile email w_member_social`

   The final set available to an application depends on the products and permissions approved in the LinkedIn Developer Portal.
7. Set `LINKEDIN_REDIRECT_URI` to the exact URI above, set `SOCIAL_MOCK_MODE=false`, and restart the backend.

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
