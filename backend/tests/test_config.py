from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.core.config import Settings


VALID_FERNET_KEY = Fernet.generate_key().decode()


def _production_settings(**overrides: str) -> Settings:
    values = {
        "_env_file": None,
        "APP_ENV": "production",
        "JWT_SECRET_KEY": "a" * 48,
        "SOCIAL_TOKEN_ENCRYPTION_KEY": VALID_FERNET_KEY,
    }
    values.update(overrides)
    return Settings(**values)


def test_valid_production_configuration_is_accepted():
    settings = _production_settings()

    settings.validate_critical_secrets()


def test_missing_production_secret_fails_with_generic_error():
    settings = _production_settings(JWT_SECRET_KEY="")

    with pytest.raises(RuntimeError, match="Critical production secrets are missing or invalid"):
        settings.validate_critical_secrets()


def test_placeholder_production_secret_fails_without_exposing_value():
    settings = _production_settings(JWT_SECRET_KEY="change-me-in-dev")

    with pytest.raises(RuntimeError, match="Critical production secrets are missing or invalid") as exc_info:
        settings.validate_critical_secrets()

    assert "change-me-in-dev" not in str(exc_info.value)


def test_local_development_defaults_remain_compatible():
    settings = Settings(
        _env_file=None,
        APP_ENV="development",
        JWT_SECRET_KEY="change-me-in-dev",
        SOCIAL_TOKEN_ENCRYPTION_KEY=VALID_FERNET_KEY,
    )

    settings.validate_critical_secrets()
    assert settings.jwt_secret_key == "change-me-in-dev"
