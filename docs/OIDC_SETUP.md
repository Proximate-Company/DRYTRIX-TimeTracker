## OpenID Connect (OIDC) Setup Guide

This guide explains how to enable Single Sign-On (SSO) with OpenID Connect for TimeTracker. OIDC is optional; you can run with local login only, OIDC only, or both.

### Quick Summary

- Set `AUTH_METHOD=oidc` (SSO only) or `AUTH_METHOD=both` (SSO + local form).
- Configure `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, and `OIDC_REDIRECT_URI`.
- Optional: Configure admin mapping via `OIDC_ADMIN_GROUP` or `OIDC_ADMIN_EMAILS`.
- Restart the app. The login page will show an “Sign in with SSO” button when enabled.

### Prerequisites

- A running TimeTracker instance (Docker or local).
- An OIDC provider (e.g., Azure AD, Okta, Keycloak, Auth0, Google Workspace).
- A client application registered at your IdP with Authorization Code flow enabled.

### 1) Application URLs

You will need these URLs when creating the OIDC client at your Identity Provider:

- Authorization callback (Redirect URI):
  - `https://<your-app-host>/auth/oidc/callback`
- Post-logout redirect (optional):
  - `https://<your-app-host>/`

Make sure your external URL and protocol (HTTP/HTTPS) match how users access the app. Behind a reverse proxy, ensure the proxy sets `X-Forwarded-Proto` so redirects/cookies work correctly.

### 2) Required Environment Variables

Add these to your environment (e.g., `.env`, Docker Compose, or Kubernetes Secrets):

```
AUTH_METHOD=oidc            # or both, or local

# Core OIDC settings
OIDC_ISSUER=https://idp.example.com/realms/your-realm
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret
OIDC_REDIRECT_URI=https://your-app.example.com/auth/oidc/callback

# Scopes and claims (defaults are usually fine)
OIDC_SCOPES=openid profile email
OIDC_USERNAME_CLAIM=preferred_username
OIDC_FULL_NAME_CLAIM=name
OIDC_EMAIL_CLAIM=email
OIDC_GROUPS_CLAIM=groups

# Optional admin mapping
OIDC_ADMIN_GROUP=timetracker-admins      # If your IdP issues a groups claim
OIDC_ADMIN_EMAILS=alice@company.com,bob@company.com

# Optional logout behavior
OIDC_POST_LOGOUT_REDIRECT_URI=https://your-app.example.com/
```

Also ensure the standard app settings are configured (database, secret key, etc.). See `env.example` for a complete template.

### 3) Provider-Specific Notes

- Azure AD (Entra ID)
  - Issuer: `https://login.microsoftonline.com/<tenant-id>/v2.0`
  - Use `openid profile email` scopes.
  - Preferred username commonly available via `preferred_username` or `upn`.
  - Group claims may need to be enabled in App Registration → Token configuration.

- Okta
  - Issuer: `https://<yourOktaDomain>/oauth2/default`
  - Add claims for `groups` if you want role mapping by group.

- Keycloak
  - Issuer: `https://<keycloak>/realms/<realm>`
  - You can map custom claims and groups in the realm client.

- Google Workspace
  - Issuer: `https://accounts.google.com`
  - Groups generally not available by default; prefer admin mapping via emails.

### 4) Behavior and Mapping

- When a user completes SSO:
  - We parse ID token and/or fetch userinfo to get `preferred_username`, `name`, `email` and optional `groups`.
  - We upsert a local user record with `username`, `full_name`, `email`, and store OIDC linkage in `oidc_issuer` + `oidc_sub`.
  - If `ALLOW_SELF_REGISTER=true` (default), unknown users are created on first login; otherwise they’re blocked.
  - Admin role can be granted if user’s groups contains `OIDC_ADMIN_GROUP` or if user’s email is in `OIDC_ADMIN_EMAILS`.

### 5) Local Login Coexistence

`AUTH_METHOD` controls the login options:

- `local`: username-only form (default, no SSO).
- `oidc`: SSO only, local form is hidden and `/login` redirects to SSO.
- `both`: show SSO button and keep local form.

### 6) Docker Compose Example

```yaml
services:
  app:
    image: ghcr.io/your-org/timetracker:latest
    environment:
      - AUTH_METHOD=oidc
      - OIDC_ISSUER=https://idp.example.com/realms/your-realm
      - OIDC_CLIENT_ID=${OIDC_CLIENT_ID}
      - OIDC_CLIENT_SECRET=${OIDC_CLIENT_SECRET}
      - OIDC_REDIRECT_URI=https://your-app.example.com/auth/oidc/callback
      - OIDC_SCOPES=openid profile email
      - OIDC_ADMIN_GROUP=timetracker-admins
      - OIDC_POST_LOGOUT_REDIRECT_URI=https://your-app.example.com/
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
    # ... other settings like ports/volumes
```

### 7) Security Recommendations

- Always use HTTPS in production.
- Set secure cookies: `SESSION_COOKIE_SECURE=true` in production.
- Keep the client secret in a secret store (not committed to git).
- Restrict `ADMIN_*` variables to trusted values only.
- Ensure your reverse proxy forwards `X-Forwarded-Proto` so redirects use HTTPS URLs.

### 8) Troubleshooting

- “SSO button doesn’t appear”
  - Check `AUTH_METHOD`. Must be `oidc` or `both`.

- “Redirect URI mismatch”
  - The `OIDC_REDIRECT_URI` must exactly match the value registered at your IdP.

- “Invalid token / missing claims”
  - Confirm scopes and claim names. Override with `OIDC_*_CLAIM` envs if your IdP uses different names.

- “User is not admin”
  - Verify `OIDC_ADMIN_GROUP` matches the group claim value, or add the user’s email to `OIDC_ADMIN_EMAILS`.

- “Logout keeps me signed in”
  - Not all IdPs support end-session. If supported, we redirect to the provider’s end-session endpoint with `post_logout_redirect_uri`.

### 9) Routes Reference

- Local login page: `GET /login` (POST for username form when enabled)
- Start OIDC login: `GET /login/oidc`
- OIDC callback: `GET /auth/oidc/callback`
- Logout: `GET /logout` (tries provider end-session if available)

### 10) Database Changes

The app includes a migration that adds the following to `users`:

- `email` (nullable)
- `oidc_issuer` (nullable)
- `oidc_sub` (nullable)
- Unique constraint on `(oidc_issuer, oidc_sub)`

If your DB wasn’t migrated automatically, run your usual migration flow.

### 11) Support

If you run into issues, capture the application logs (including the IdP error page if any) and verify your env vars. Most problems are due to a mismatch in redirect URI, missing scopes/claims, or proxy/HTTPS configuration.


