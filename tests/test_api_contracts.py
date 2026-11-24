# tests/test_api_contracts.py
import pytest
from tests.conftest import mt5_mock


# ==========================================
# 1. /account-info
# ==========================================

def test_account_info_success(client, auth_headers):
    payload = {
        "username": 123456,
        "password": "secret_password",
        "server": "MetaQuotes-Demo"
    }
    response = client.post("/account-info", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["login"] == 123456
    assert data["balance"] == 10000.0
    assert "leverage" in data
    assert "equity" in data


def test_account_info_failure_502(client, auth_headers):
    mt5_mock.fail_account_info = True
    payload = {
        "username": 123456,
        "password": "wrong_password",
        "server": "MetaQuotes-Demo"
    }
    response = client.post("/account-info", headers=auth_headers, json=payload)
    assert response.status_code == 502
    assert response.get_json() == {"error": "could not fetch account info, check credentials/connection"}


def test_account_info_exception_500(client, auth_headers):
    # Passing invalid username type (e.g. string that cannot convert to int) triggers Exception
    payload = {
        "username": "not_an_int",
        "password": "password",
        "server": "MetaQuotes-Demo"
    }
    response = client.post("/account-info", headers=auth_headers, json=payload)
    assert response.status_code == 500
    assert "error" in response.get_json()


# ==========================================
# 2. /positions
# ==========================================

def test_positions_success_all(client, auth_headers):
    payload = {
        "username": 123456,
        "password": "password",
        "server": "Demo-Server"
    }
    response = client.post("/positions", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ticket"] == 123456
    assert data[0]["symbol"] == "EURUSD"


def test_positions_success_with_symbol(client, auth_headers):
    payload = {
        "username": 123456,
        "password": "password",
        "server": "Demo-Server",
        "symbol": "EURUSD"
    }
    response = client.post("/positions", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["symbol"] == "EURUSD"


def test_positions_empty_symbol_filter(client, auth_headers):
    payload = {
        "username": 123456,
        "password": "password",
        "server": "Demo-Server",
        "symbol": "GBPUSD"
    }
    response = client.post("/positions", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data == []


def test_positions_exception_500(client, auth_headers):
    payload = {
        "username": "invalid_int",
        "password": "password",
        "server": "Demo-Server"
    }
    response = client.post("/positions", headers=auth_headers, json=payload)
    assert response.status_code == 500
    assert "error" in response.get_json()


# ==========================================
# 3. /history
# ==========================================

def test_history_success_default_dates(client, auth_headers):
    payload = {
        "username": 123456,
        "password": "password",
        "server": "Demo-Server"
    }
    response = client.post("/history", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ticket"] == 987654
    assert data[0]["profit"] == 25.0


def test_history_success_custom_dates(client, auth_headers):
    payload = {
        "username": 123456,
        "password": "password",
        "server": "Demo-Server",
        "from": "2026-10-01T00:00:00",
        "to": "2026-11-01T00:00:00"
    }
    response = client.post("/history", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1


def test_history_exception_500(client, auth_headers):
    payload = {
        "username": 123456,
        "password": "password",
        "server": "Demo-Server",
        "from": "invalid_date_format"
    }
    response = client.post("/history", headers=auth_headers, json=payload)
    assert response.status_code == 500
    assert "error" in response.get_json()


# ==========================================
# 4. /trade
# ==========================================

def test_trade_success_buy(client, auth_headers):
    payload = {
        "platform": "Metatrader",
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "hedge": True,
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1,
        "sl": 1.0450,
        "tp": 1.0600,
        "comment": "test trade",
        "type_time": "gtc",
        "type_filling": "ioc"
    }
    response = client.post("/trade", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["retcode"] == 10009
    assert data["order"] == 22222


def test_trade_success_sell(client, auth_headers):
    payload = {
        "platform": "Metatrader",
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "hedge": True,
        "symbol": "EURUSD",
        "side": "sell",
        "volume": 0.2,
        "type_time": "day",
        "type_filling": "fok"
    }
    response = client.post("/trade", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["retcode"] == 10009


def test_trade_validation_error_400(client, auth_headers):
    # Missing required field "symbol" and "side"
    payload = {
        "platform": "Metatrader",
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "hedge": True,
        "volume": 0.1
    }
    response = client.post("/trade", headers=auth_headers, json=payload)
    assert response.status_code == 400


def test_trade_order_send_none_retcode(client, auth_headers):
    mt5_mock.order_send_none = True
    payload = {
        "platform": "Metatrader",
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "hedge": True,
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1
    }
    response = client.post("/trade", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["retcode"] is None
    assert "order_send returned None" in data["comment"]


def test_trade_tick_failure_500(client, auth_headers):
    mt5_mock.fail_tick = True
    payload = {
        "platform": "Metatrader",
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "hedge": True,
        "symbol": "EURUSD",
        "side": "buy",
        "volume": 0.1
    }
    response = client.post("/trade", headers=auth_headers, json=payload)
    assert response.status_code == 500
    assert "error" in response.get_json()
    assert "Could not get tick" in response.get_json()["error"]


# ==========================================
# 5. /close-position
# ==========================================

def test_close_position_success(client, auth_headers):
    payload = {
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "ticket": 123456,
        "comment": "closing ticket"
    }
    response = client.post("/close-position", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["retcode"] == 10009


def test_close_position_not_found_500(client, auth_headers):
    payload = {
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "ticket": 99999999  # nonexistent ticket
    }
    response = client.post("/close-position", headers=auth_headers, json=payload)
    assert response.status_code == 500
    assert "No open position with ticket" in response.get_json()["error"]


def test_close_position_validation_error_400(client, auth_headers):
    payload = {
        "server": "Demo-Server",
        "username": "123456"
        # missing ticket and password
    }
    response = client.post("/close-position", headers=auth_headers, json=payload)
    assert response.status_code == 400


# ==========================================
# 6. /modify-position
# ==========================================

def test_modify_position_success(client, auth_headers):
    payload = {
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "ticket": 123456,
        "sl": 1.0420,
        "tp": 1.0650
    }
    response = client.post("/modify-position", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["retcode"] == 10009


def test_modify_position_not_found_500(client, auth_headers):
    payload = {
        "server": "Demo-Server",
        "username": "123456",
        "password": "password",
        "ticket": 99999999
    }
    response = client.post("/modify-position", headers=auth_headers, json=payload)
    assert response.status_code == 500
    assert "No open position with ticket" in response.get_json()["error"]


# ==========================================
# 7. /info
# ==========================================

def test_info_success(client, auth_headers):
    payload = {
        "username": "123456",
        "password": "password",
        "server": "Demo-Server",
        "symbols": {
            "EURUSD": 60
        },
        "timeframes": {
            "m1": 0
        }
    }
    response = client.post("/info", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "EURUSD" in data
    assert "m1" in data["EURUSD"]
    candles = data["EURUSD"]["m1"]
    assert isinstance(candles, list)
    assert len(candles) == 1
    assert "time" in candles[0]
    assert candles[0]["open"] == 1.0500


def test_info_error_preserves_200(client, auth_headers):
    # When an error occurs in info (e.g. invalid username), existing code catches and returns partial result with 200
    payload = {
        "username": "invalid_int",
        "password": "password",
        "server": "Demo-Server",
        "symbols": {
            "EURUSD": 60
        },
        "timeframes": {
            "m1": 0
        }
    }
    response = client.post("/info", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
