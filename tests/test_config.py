"""Tests for the Settings configuration class and app factory integration."""

import pytest
from pydantic import ValidationError

from fathom.app import create_app
from fathom.config import Settings


class TestSettingsDefaults:
    """Verify Settings provides sensible defaults with no env vars."""

    def test_secret_key_default(self):
        """Default secret_key is the dev key string."""
        expected = "fathom-dev-key"
        settings = Settings()
        assert settings.secret_key == expected

    def test_host_default(self):
        """Default host is localhost."""
        settings = Settings()
        assert settings.host == "127.0.0.1"

    def test_port_default(self):
        """Default port is 5000."""
        settings = Settings()
        assert settings.port == 5000

    def test_debug_default(self):
        """Debug is disabled by default."""
        settings = Settings()
        assert settings.debug is False

    def test_workers_default(self):
        """Default worker count is 2."""
        settings = Settings()
        assert settings.workers == 2

    def test_default_return_rate(self):
        """Default return rate is 7%."""
        settings = Settings()
        assert settings.default_return_rate == 0.07

    def test_default_inflation_rate(self):
        """Default inflation rate is 3%."""
        settings = Settings()
        assert settings.default_inflation_rate == 0.03

    def test_default_tax_rate(self):
        """Default tax rate is 22%."""
        settings = Settings()
        assert settings.default_tax_rate == 0.22


class TestSettingsEnvOverride:
    """Verify FATHOM_-prefixed env vars override defaults."""

    def test_port_override(self, monkeypatch):
        """FATHOM_PORT=8080 sets port to 8080."""
        monkeypatch.setenv("FATHOM_PORT", "8080")
        settings = Settings()
        assert settings.port == 8080

    def test_secret_key_override(self, monkeypatch):
        """FATHOM_SECRET_KEY overrides the default key."""
        expected = "prod-key-12345"
        monkeypatch.setenv("FATHOM_SECRET_KEY", expected)
        settings = Settings()
        assert settings.secret_key == expected

    def test_debug_override(self, monkeypatch):
        """FATHOM_DEBUG=true enables debug mode."""
        monkeypatch.setenv("FATHOM_DEBUG", "true")
        settings = Settings()
        assert settings.debug is True

    def test_default_return_rate_override(self, monkeypatch):
        """FATHOM_DEFAULT_RETURN_RATE overrides the 7% default."""
        monkeypatch.setenv("FATHOM_DEFAULT_RETURN_RATE", "0.10")
        settings = Settings()
        assert settings.default_return_rate == 0.10


class TestSettingsValidation:
    """Verify invalid env var values raise ValidationError on startup."""

    def test_invalid_port_raises(self, monkeypatch):
        """Non-numeric FATHOM_PORT raises ValidationError."""
        monkeypatch.setenv("FATHOM_PORT", "abc")
        with pytest.raises(ValidationError):
            Settings()

    def test_invalid_debug_raises(self, monkeypatch):
        """Non-boolean FATHOM_DEBUG raises ValidationError."""
        monkeypatch.setenv("FATHOM_DEBUG", "not-a-bool")
        with pytest.raises(ValidationError):
            Settings()


class TestAppFactoryIntegration:
    """Verify create_app wires Settings into Flask app config."""

    def test_create_app_with_custom_settings(self):
        """Custom Settings values propagate to Flask app config."""
        custom_key = "test-key-value"
        settings = Settings(secret_key=custom_key, port=9999)
        app = create_app(settings)
        assert app.config["SECRET_KEY"] == custom_key

    def test_create_app_stores_settings(self):
        """Settings instance is stored in app.config FATHOM_SETTINGS."""
        settings = Settings()
        app = create_app(settings)
        assert app.config["FATHOM_SETTINGS"] is settings

    def test_create_app_default_settings(self):
        """create_app() without args creates its own Settings."""
        app = create_app()
        assert "FATHOM_SETTINGS" in app.config
        assert isinstance(app.config["FATHOM_SETTINGS"], Settings)
