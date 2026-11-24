# src/api/middleware.py
import hmac
from functools import wraps
from flask import request, jsonify
from config.settings import settings
from src.utils.logger import logger


def token_required(f):
    """Decorator to enforce token-based authentication via 'token' header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("token")
        expected_token = settings.auth_token

        # If server token is not configured or client provided no token, reject
        if not token or not expected_token:
            return jsonify({"message": "Authorization exception"}), 401

        # Timing-attack safe comparison
        if not hmac.compare_digest(token.strip(), expected_token.strip()):
            return jsonify({"message": "Authorization exception"}), 401

        return f(*args, **kwargs)

    return decorated


def auth():
    """Legacy backward-compatible wrapper matching `auth()` usage."""
    def decorator(f):
        return token_required(f)

    return decorator
