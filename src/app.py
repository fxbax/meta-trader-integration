# src/app.py
from flask import Flask
from flask_cors import CORS
from config.settings import settings
from src.api.routes import api_bp
from src.utils.logger import logger


def create_app(custom_settings=None) -> Flask:
    """Application factory for Flask app."""
    app = Flask(__name__)
    CORS(app)

    # Optional Sentry initialization if configured
    dsn = custom_settings.sentry_dsn if custom_settings else settings.sentry_dsn
    if dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            sentry_sdk.init(
                dsn=dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=1.0,
            )
            logger.info("Sentry monitoring initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize Sentry: {e}")

    # Register API blueprint
    app.register_blueprint(api_bp)

    return app
