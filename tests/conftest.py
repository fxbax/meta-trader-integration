import ast
import sys
from unittest.mock import MagicMock
import pytest

# Python 3.14 compatibility shim for Werkzeug 2.2.2
if not hasattr(ast, "Str"):
    class StrShim(ast.Constant):
        def __init__(self, s="", **kwargs):
            super().__init__(value=s, **kwargs)
            self.s = s

        @property
        def value(self):
            return self.s

        @value.setter
        def value(self, val):
            self.s = val

    ast.Str = StrShim


# Define comprehensive MetaTrader5 Mock
class MockAccountInfo:
    def __init__(self, login=123456):
        self.login = login
        self.trade_mode = 0
        self.leverage = 100
        self.balance = 10000.0
        self.equity = 10000.0
        self.profit = 0.0

    def _asdict(self):
        return {
            "login": self.login,
            "trade_mode": self.trade_mode,
            "leverage": self.leverage,
            "balance": self.balance,
            "equity": self.equity,
            "profit": self.profit,
        }


class MockPosition:
    def __init__(self, ticket=123456, symbol="EURUSD", p_type=0, volume=0.1, sl=1.0450, tp=1.0600):
        self.ticket = ticket
        self.symbol = symbol
        self.type = p_type
        self.volume = volume
        self.sl = sl
        self.tp = tp

    def _asdict(self):
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "type": self.type,
            "volume": self.volume,
            "sl": self.sl,
            "tp": self.tp,
        }


class MockDeal:
    def __init__(self, ticket=987654, symbol="EURUSD", volume=0.1, profit=25.0):
        self.ticket = ticket
        self.symbol = symbol
        self.volume = volume
        self.profit = profit

    def _asdict(self):
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "volume": self.volume,
            "profit": self.profit,
        }


class MockTick:
    def __init__(self, ask=1.0550, bid=1.0548, time=1700000000):
        self.ask = ask
        self.bid = bid
        self.time = time


class MockOrderResult:
    def __init__(self, retcode=10009, deal=11111, order=22222, volume=0.1, price=1.0550, comment=""):
        self.retcode = retcode
        self.deal = deal
        self.order = order
        self.volume = volume
        self.price = price
        self.comment = comment

    def _asdict(self):
        return {
            "retcode": self.retcode,
            "deal": self.deal,
            "order": self.order,
            "volume": self.volume,
            "price": self.price,
            "comment": self.comment,
        }


class MockSymbolInfo:
    def __init__(self, point=0.00001):
        self.point = point


class MetaTrader5MockModule:
    # Constants
    ORDER_TIME_GTC = 0
    ORDER_TIME_DAY = 1
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    POSITION_TYPE_BUY = 0
    POSITION_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_SLTP = 6

    TIMEFRAME_M1 = 1
    TIMEFRAME_M2 = 2
    TIMEFRAME_M3 = 3
    TIMEFRAME_M4 = 4
    TIMEFRAME_M5 = 5
    TIMEFRAME_M6 = 6
    TIMEFRAME_M10 = 10
    TIMEFRAME_M12 = 12
    TIMEFRAME_M15 = 15
    TIMEFRAME_M20 = 20
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H2 = 16386
    TIMEFRAME_H3 = 16387
    TIMEFRAME_H4 = 16388
    TIMEFRAME_H6 = 16390
    TIMEFRAME_H8 = 16392
    TIMEFRAME_H12 = 16396
    TIMEFRAME_D1 = 16408
    TIMEFRAME_W1 = 32769
    TIMEFRAME_MN1 = 49153

    def __init__(self):
        self.reset()

    def reset(self):
        self._last_error = (1, "Success")
        self.fail_login = False
        self.fail_account_info = False
        self.fail_tick = False
        self.fail_order_send = False
        self.order_send_none = False
        self.positions = [
            MockPosition(ticket=123456, symbol="EURUSD", p_type=0, volume=0.1, sl=1.0450, tp=1.0600)
        ]
        self.deals = [
            MockDeal(ticket=987654, symbol="EURUSD", volume=0.1, profit=25.0)
        ]
        self.rates = [
            {
                'time': 1700000000,
                'open': 1.0500,
                'high': 1.0520,
                'low': 1.0490,
                'close': 1.0515,
                'tick_volume': 100,
                'spread': 1
            }
        ]

    def initialize(self, *args, **kwargs):
        return True

    def login(self, login=None, password=None, server=None, path=None):
        if self.fail_login:
            self._last_error = (-1, "Invalid credentials")
            return False
        return True

    def shutdown(self):
        return True

    def last_error(self):
        return self._last_error

    def account_info(self):
        if self.fail_account_info:
            return None
        return MockAccountInfo()

    def positions_get(self, symbol=None, ticket=None):
        if ticket is not None:
            matches = [p for p in self.positions if p.ticket == int(ticket)]
            return tuple(matches) if matches else ()
        if symbol is not None:
            matches = [p for p in self.positions if p.symbol == symbol]
            return tuple(matches)
        return tuple(self.positions)

    def history_deals_get(self, date_from, date_to):
        return tuple(self.deals)

    def symbol_select(self, symbol, enable=True):
        return True

    def symbol_info_tick(self, symbol):
        if self.fail_tick:
            return None
        return MockTick()

    def symbol_info(self, symbol):
        return MockSymbolInfo()

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        return self.rates

    def order_send(self, request):
        if self.order_send_none:
            self._last_error = (10013, "Invalid request")
            return None
        return MockOrderResult(
            retcode=10009,
            deal=11111,
            order=22222,
            volume=request.get("volume", 0.1),
            price=request.get("price", 1.0550),
            comment=request.get("comment", "")
        )


# Register mock module before any imports
mt5_mock = MetaTrader5MockModule()
sys.modules["MetaTrader5"] = mt5_mock


@pytest.fixture(autouse=True)
def reset_mt5_mock():
    mt5_mock.reset()
    yield mt5_mock


TEST_AUTH_TOKEN = "test-secret-auth-token-xyz-123"


@pytest.fixture
def app(monkeypatch):
    from config.settings import settings
    monkeypatch.setattr(settings, "auth_token", TEST_AUTH_TOKEN)

    import utils.tools
    monkeypatch.setattr(utils.tools, "getEnvValue", lambda key: TEST_AUTH_TOKEN if key == "AUTH_TOKEN" else None)
    
    import main
    monkeypatch.setattr(main, "getEnvValue", lambda key: TEST_AUTH_TOKEN if key == "AUTH_TOKEN" else None)
    
    main.app.config["TESTING"] = True
    return main.app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    return {"token": TEST_AUTH_TOKEN}
