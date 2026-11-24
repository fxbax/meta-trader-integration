# run.py
import argparse
import sys
from config.settings import settings
from src.app import create_app
from src.utils.logger import logger, setup_logger


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MetaTrader 5 Integration API Server"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=None,
        help="Port to listen on (1-65535, default from config or 5000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address to bind to (default from config or 0.0.0.0)"
    )
    parser.add_argument(
        "-t", "--token",
        type=str,
        default=None,
        help="API access token (AUTH_TOKEN override)"
    )
    parser.add_argument(
        "-l", "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Logging level"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Number of worker threads for production server (default: 4)"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        default=False,
        help="Run in Flask development mode instead of production Waitress"
    )
    return parser.parse_args(args)


def apply_cli_overrides(parsed_args):
    """Apply CLI arguments to global settings."""
    if parsed_args.port is not None:
        if not (1 <= parsed_args.port <= 65535):
            print(f"Error: Port must be between 1 and 65535, got {parsed_args.port}", file=sys.stderr)
            sys.exit(1)
        settings.port = parsed_args.port

    if parsed_args.host is not None:
        settings.host = parsed_args.host

    if parsed_args.token is not None:
        settings.auth_token = parsed_args.token

    if parsed_args.log_level is not None:
        settings.log_level = parsed_args.log_level
        setup_logger()


def main():
    """Main entrypoint for starting the application."""
    args = parse_args()
    apply_cli_overrides(args)

    app = create_app()

    # Warn if auth token is empty
    if not settings.auth_token:
        logger.warning(
            "⚠️ AUTH_TOKEN is not set! All authenticated requests will be rejected with 401 until a token is configured."
        )
    else:
        logger.info("Security: AUTH_TOKEN configured.")

    if args.dev:
        logger.info(f"Starting in DEVELOPMENT mode on http://{settings.host}:{settings.port}")
        app.run(host=settings.host, port=settings.port, debug=True)
    else:
        logger.info(
            f"Starting in PRODUCTION mode (Waitress WSGI with {args.threads} threads) on http://{settings.host}:{settings.port}"
        )
        try:
            from waitress import serve
            serve(app, host=settings.host, port=settings.port, threads=args.threads)
        except ImportError:
            logger.warning("Waitress is not installed, falling back to Flask runner...")
            app.run(host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
