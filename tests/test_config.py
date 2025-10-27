import pytest
from pydantic import ValidationError

from app.config import Settings, SettingsConfigDict


def test_settings_load_database_url_from_env(monkeypatch):
    """
    Tests settings loads DATABASE_URL from the environment variable.
    """
    postgresl_url = "postgresql://env_user:env_pass@env_host/env_db"
    monkeypatch.setenv("DATABASE_URL", postgresl_url)

    monkeypatch.setenv("SECRET_KEY", "dummy-secret-for-this-test")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("ALGORITHM", "test-algo")

    settings = Settings()

    assert settings.DATABASE_URL == postgresl_url
    assert settings.SECRET_KEY == "dummy-secret-for-this-test"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert settings.ALGORITHM == "test-algo"


def test_settings_use_default_database_url(monkeypatch):
    """
    Test settigns uses the default DATABASE_URL when non is provided.
    """
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "dummy-secret-for-this-test-default")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "20")
    monkeypatch.setenv("ALGORITHM", "test-algo")

    original_config = Settings.model_config
    monkeypatch.setattr(
        Settings, "model_config", SettingsConfigDict(env_file=None, extra="ignore")
    )

    try:
        settings = Settings()
        assert settings.DATABASE_URL == "sqlite:///:memory:"
        assert settings.SECRET_KEY == "dummy-secret-for-this-test-default"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 20
        assert settings.ALGORITHM == "test-algo"
        assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
    finally:
        monkeypatch.setattr(Settings, "model_config", original_config)


def test_validation_thrown_when_missing_config(monkeypatch):
    """
    Tests that Pydantic throws a ValidationError when there is amissing
    environment variable.
    """

    monkeypatch.delenv("ALGORITHM", raising=False)
    monkeypatch.setenv("SECRET_KEY", "one-more-time")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "20")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/db")

    original_config = Settings.model_config
    monkeypatch.setattr(
        Settings, "model_config", SettingsConfigDict(env_file=None, extra="ignore")
    )

    try:
        with pytest.raises(ValidationError) as excinfo:
            Settings()
        assert "ALGORITHM" in str(excinfo.value)
        assert "Field required" in str(excinfo.value)
    finally:
        monkeypatch.setattr(Settings, "model_config", original_config)
