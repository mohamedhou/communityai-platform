from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    key = settings.social_token_encryption_key
    if not key or not key.strip():
        raise ValueError("SOCIAL_TOKEN_ENCRYPTION_KEY is not configured in .env")
    try:
        return Fernet(key.encode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid SOCIAL_TOKEN_ENCRYPTION_KEY: {exc}") from exc


def encrypt_token(token: str | None) -> str | None:
    if token is None:
        return None
    fernet = _get_fernet()
    return fernet.encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str | None) -> str | None:
    if encrypted_token is None:
        return None
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
