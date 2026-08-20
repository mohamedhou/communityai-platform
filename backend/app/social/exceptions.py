from __future__ import annotations


class SocialProviderError(Exception):
    """Exception raised for errors during OAuth code exchange or API calls to social platforms."""

    pass


class OAuthStateExpiredOrInvalid(Exception):
    """Exception raised when OAuth state validation fails (e.g. CSRF check failed or expired)."""

    pass
