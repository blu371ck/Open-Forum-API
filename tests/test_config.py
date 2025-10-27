import pytest
from pydantic import ValidationError

from app.config import Settings, SettingsConfigDict


def test_settings_load_from_env(monkeypatch):
    """
    Tests that settings correctly load required variables from the .env file.
    """
    monkeypatch.setenv("SECRET_KEY", "test-secret-from-env")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "45")

    settings = Settings()
    assert settings.SECRET_KEY == "test-secret-from-env"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 45
    assert settings.ALGORITHM == "HS256"


def test_settings_Missing_required_variable(monkeypatch):
    """
    Tests that settings raises a ValidationError if a required env variable is missing.
    """
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

    original_config = Settings.model_config
    monkeypatch.setattr(
        Settings, "model_config", SettingsConfigDict(env_file=None, extra="ignore")
    )

    try:
        with pytest.raises(ValidationError) as excinfo:
            Settings()

        assert "SECRET_KEY" in str(excinfo.value)
        assert "Field required" in str(excinfo.value)
    finally:
        monkeypatch.setattr(Settings, "model_config", original_config)


def test_settings_type_coercion(monkeypatch):
    """
    Tests that Pydantic correctly converts env var strings to declared types (e.g., int)
    """
    monkeypatch.setenv("SECRET_KEY", "another-secret")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

    settings = Settings()

    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
    assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
