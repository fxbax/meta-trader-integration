# tests/test_cli.py
import pytest
from run import parse_args, apply_cli_overrides
from config.settings import settings


def test_parse_args_defaults():
    args = parse_args([])
    assert args.port is None
    assert args.host is None
    assert args.token is None
    assert args.log_level is None
    assert args.threads == 4
    assert args.dev is False


def test_parse_args_custom_values():
    args = parse_args([
        "--port", "7000",
        "--host", "127.0.0.1",
        "--token", "secret-cli-token",
        "--log-level", "DEBUG",
        "--threads", "8",
        "--dev"
    ])
    assert args.port == 7000
    assert args.host == "127.0.0.1"
    assert args.token == "secret-cli-token"
    assert args.log_level == "DEBUG"
    assert args.threads == 8
    assert args.dev is True


def test_apply_cli_overrides():
    args = parse_args(["-p", "6000", "-t", "new-token", "--host", "0.0.0.0"])
    apply_cli_overrides(args)
    assert settings.port == 6000
    assert settings.auth_token == "new-token"
    assert settings.host == "0.0.0.0"


def test_apply_cli_overrides_invalid_port():
    args = parse_args(["-p", "99999"])
    with pytest.raises(SystemExit):
        apply_cli_overrides(args)
