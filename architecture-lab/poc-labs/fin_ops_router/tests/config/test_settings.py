import os
from unittest.mock import patch

from finops_llm_router.config.settings import Settings


def test_settings_defaults_when_env_missing():
    """Settings should fall back to default values when env vars are not set."""
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()

        assert settings.DB_URL == "sqlite:///telemetry.db"
        assert settings.LOG_LEVEL == "INFO"


def test_settings_reads_environment_variables():
    """Settings should read DB_URL and LOG_LEVEL from environment variables."""
    env = {
        "DB_URL": "postgresql://localhost:5432/mydb",
        "LOG_LEVEL": "DEBUG",
    }

    with patch.dict(os.environ, env, clear=True):
        settings = Settings()

        assert settings.DB_URL == "postgresql://localhost:5432/mydb"
        assert settings.LOG_LEVEL == "DEBUG"


def test_settings_partial_env_fallback():
    """If only one env var is set, the other should fall back to default."""
    with patch.dict(os.environ, {"DB_URL": "mysql://db"}, clear=True):
        settings = Settings()

        assert settings.DB_URL == "mysql://db"
        assert settings.LOG_LEVEL == "INFO"  # default fallback
