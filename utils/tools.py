# utils/tools.py
from config.settings import settings


def getEnvValue(key: str):
    """Retrieve environment/config value with backward-compatibility for legacy callers."""
    if key == "AUTH_TOKEN":
        return settings.auth_token
    if key in ("PORT", "port"):
        return settings.port
    if key in ("HOST", "host"):
        return settings.host
    if key in ("SENTRY_DSN", "SENTRY_DNS"):
        return settings.sentry_dsn
    if key == "LOG_LEVEL":
        return settings.log_level
    return getattr(settings, key.lower(), None)
