# config/settings.py
import os
from pathlib import Path
from typing import Optional
from dotenv import dotenv_values, load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    # Fallback to load whatever .env might be in current working directory
    load_dotenv()


class Settings:
    """Application settings with prioritized resolution:
    1. Direct override / constructor args
    2. Environment variables (os.environ)
    3. .env file
    4. Default values
    """

    def __init__(
        self,
        port: Optional[int] = None,
        host: Optional[str] = None,
        auth_token: Optional[str] = None,
        log_level: Optional[str] = None,
        log_dir: Optional[str] = None,
        sentry_dsn: Optional[str] = None,
    ):
        # Read .env values as fallback
        dotenv_dict = dotenv_values(_env_path) if _env_path.exists() else {}

        # Resolve Port
        raw_port = (
            port
            or os.environ.get("PORT")
            or dotenv_dict.get("PORT")
            or 5000
        )
        try:
            self.port = int(raw_port)
        except (ValueError, TypeError):
            self.port = 5000

        # Resolve Host
        self.host = (
            host
            or os.environ.get("HOST")
            or dotenv_dict.get("HOST")
            or "0.0.0.0"
        )

        # Resolve Auth Token
        self.auth_token = (
            auth_token
            or os.environ.get("AUTH_TOKEN")
            or dotenv_dict.get("AUTH_TOKEN")
            or ""
        )

        # Resolve Logging
        self.log_level = (
            log_level
            or os.environ.get("LOG_LEVEL")
            or dotenv_dict.get("LOG_LEVEL")
            or "INFO"
        ).upper()

        self.log_dir = Path(
            log_dir
            or os.environ.get("LOG_DIR")
            or dotenv_dict.get("LOG_DIR")
            or (BASE_DIR / "logs")
        )

        # Resolve Sentry DSN
        self.sentry_dsn = (
            sentry_dsn
            or os.environ.get("SENTRY_DSN")
            or os.environ.get("SENTRY_DNS")  # support legacy typo
            or dotenv_dict.get("SENTRY_DSN")
            or dotenv_dict.get("SENTRY_DNS")
            or ""
        )

    def reload(self):
        """Reload settings from disk/environment."""
        if _env_path.exists():
            load_dotenv(dotenv_path=_env_path, override=True)
        self.__init__()


# Global singleton instance
settings = Settings()
