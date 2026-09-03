from __future__ import annotations


class AIProviderError(Exception):
    """Raised when an AI provider encounters an error (rate limit, quota, network, auth)."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
