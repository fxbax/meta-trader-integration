# tests/test_settings.py
import os
from config.settings import Settings


def test_settings_default_values():
    settings = Settings(port=5000, host="0.0.0.0", auth_token="my-token")
    assert settings.port == 5000
    assert settings.host == "0.0.0.0"
    assert settings.auth_token == "my-token"


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("AUTH_TOKEN", "env-token-secret")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()
    assert settings.port == 8080
    assert settings.host == "127.0.0.1"
    assert settings.auth_token == "env-token-secret"
    assert settings.log_level == "DEBUG"


def test_settings_invalid_port_fallback(monkeypatch):
    monkeypatch.setenv("PORT", "not-a-port")
    settings = Settings()
    assert settings.port == 5000
