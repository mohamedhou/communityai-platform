from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _fernet_from_settings(settings) -> Fernet:
    key = settings.social_token_encryption_key
    if not key or not key.strip():
        raise ValueError("SOCIAL_TOKEN_ENCRYPTION_KEY is not configured in .env")
    try:
        return Fernet(key.encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise ValueError("SOCIAL_TOKEN_ENCRYPTION_KEY is invalid") from exc


def validate_encryption_key() -> None:
    _fernet_from_settings(get_settings())


def is_encryption_key_valid(settings=None) -> bool:
    try:
        _fernet_from_settings(settings or get_settings())
    except ValueError:
        return False
    return True


def _get_fernet() -> Fernet:
    return _fernet_from_settings(get_settings())


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
