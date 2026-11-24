# tests/test_mt5_client.py
import pytest
from src.services.mt5_client import MT5Client
from src.services.exceptions import MT5ConnectionError
from tests.conftest import mt5_mock


def test_mt5_client_connect_success():
    client = MT5Client(username=123456, password="pw", server="Demo")
    assert client.get_account_info() is not None


def test_mt5_client_connect_failure_raises():
    mt5_mock.fail_login = True
    with pytest.raises(MT5ConnectionError):
        MT5Client(username=123456, password="wrong", server="Demo")


def test_mt5_client_positions():
    client = MT5Client(username=123456, password="pw", server="Demo")
    positions = client.get_positions()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "EURUSD"


def test_mt5_client_map_timeframe():
    client = MT5Client()
    tf_map = client.map_timeframe()
    assert "m1" in tf_map
    assert "1h" in tf_map
    assert "1d" in tf_map
