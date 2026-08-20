from datetime import datetime

import MetaTrader5 as mt5
import pandas as pd

from service.BaseService import BaseService


class Metatrader(BaseService):
    def __init__(self, symbol=None, username=None, password=None, server=None, path=None) -> None:
        self.mt = mt5
        self.symbol = symbol
        self.connect(
            login=int(username),
            password=password,
            server=server,
            path=path
        )

    def connect(self, login=None, password=None, server=None, path=None):
        account = int(login)
        self.mt.initialize(server=server, login=login, password=password)
        authorized = self.mt.login(
            login=account, server=server, password=password, path=path)
        if authorized:
            return self.mt
        else:
            print("Failed to connect at account #{}, error code: {}".format(
                account, mt5.last_error()))
            mt5.shutdown()

    def set_symbol(self, symbol):
        self.symbol = symbol
        return self

    def get_account_info(self):
        return self.mt.account_info()

    def get_positions(self, symbol=None):
        positions = self.mt.positions_get(symbol=symbol) if symbol else self.mt.positions_get()
        if positions is None:
            return []
        return [position._asdict() for position in positions]

    def get_history(self, date_from, date_to):
        deals = self.mt.history_deals_get(date_from, date_to)
        if deals is None:
            return []
        return [deal._asdict() for deal in deals]

    # Maps the wire values of resource/Requests.py's TypeTime/TypeFilling
    # enums to the real MT5 order_send() constants. Previously hardcoded
    # here as ORDER_TIME_GTC / ORDER_FILLING_IOC — those are still the
    # fallback defaults if a caller omits the field or sends something
    # unrecognized, so behavior for an unconfigured caller is unchanged.
    def _order_time_constant(self, value):
        mapping = {
            "gtc": self.mt.ORDER_TIME_GTC,
            "day": self.mt.ORDER_TIME_DAY,
        }
        # accept either the raw string or a (str, Enum) member — both compare
        # equal to their string value, but normalize explicitly to be safe.
        value = getattr(value, "value", value)
        return mapping.get(value, self.mt.ORDER_TIME_GTC)

    def _order_filling_constant(self, value):
        mapping = {
            "fok": self.mt.ORDER_FILLING_FOK,
            "ioc": self.mt.ORDER_FILLING_IOC,
            "return": self.mt.ORDER_FILLING_RETURN,
        }
        value = getattr(value, "value", value)
        return mapping.get(value, self.mt.ORDER_FILLING_IOC)

    def trade(self, data):
        # One order per call — the caller (Laravel) sends a single side/volume/sl/tp
        # per request, matching the app's real AI signal shape (see resource/Requests.py).
        symbol = data["symbol"]
        self.mt.symbol_select(symbol, True)
        tick = self.mt.symbol_info_tick(symbol)
        if tick is None:
            raise Exception("Could not get tick for " + symbol)

        side = data["side"]
        volume = data["volume"]
        sl = data.get("sl")
        tp = data.get("tp")
        comment = data.get("comment") or "fxbax"

        order_type = self.mt.ORDER_TYPE_BUY if side == "buy" else self.mt.ORDER_TYPE_SELL
        price = tick.ask if side == "buy" else tick.bid

        request = {
            "action": self.mt.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "sl": float(sl) if sl else 0.0,
            "tp": float(tp) if tp else 0.0,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": self._order_time_constant(data.get("type_time", "gtc")),
            "type_filling": self._order_filling_constant(data.get("type_filling", "ioc")),
        }

        result = self.mt.order_send(request)
        if result is None:
            return {"retcode": None, "comment": "order_send returned None, error: " + str(mt5.last_error())}
        return result._asdict()

    def _find_position(self, ticket):
        positions = self.mt.positions_get(ticket=int(ticket))
        if not positions:
            raise Exception("No open position with ticket " + str(ticket))
        return positions[0]

    def close_position(self, ticket, comment=None):
        # Closing = an opposite-side market deal that carries the "position"
        # key. Without that key MT5 would open a NEW (hedged) position instead
        # of closing this one.
        position = self._find_position(ticket)
        symbol = position.symbol

        self.mt.symbol_select(symbol, True)
        tick = self.mt.symbol_info_tick(symbol)
        if tick is None:
            raise Exception("Could not get tick for " + symbol)

        closing_buy = position.type == self.mt.POSITION_TYPE_BUY
        order_type = self.mt.ORDER_TYPE_SELL if closing_buy else self.mt.ORDER_TYPE_BUY
        price = tick.bid if closing_buy else tick.ask

        request = {
            "action": self.mt.TRADE_ACTION_DEAL,
            "position": int(ticket),
            "symbol": symbol,
            "volume": float(position.volume),
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": comment or "fxbax-close",
            "type_time": self.mt.ORDER_TIME_GTC,
            "type_filling": self.mt.ORDER_FILLING_IOC,
        }

        result = self.mt.order_send(request)
        if result is None:
            return {"retcode": None, "comment": "order_send returned None, error: " + str(mt5.last_error())}
        return result._asdict()

    def modify_position(self, ticket, sl=None, tp=None):
        # TRADE_ACTION_SLTP replaces BOTH levels in one shot, and 0.0 means
        # "remove the level" — so a side the caller didn't send is filled in
        # from the live position to keep it unchanged.
        position = self._find_position(ticket)

        request = {
            "action": self.mt.TRADE_ACTION_SLTP,
            "position": int(ticket),
            "symbol": position.symbol,
            "sl": float(sl) if sl is not None else float(position.sl),
            "tp": float(tp) if tp is not None else float(position.tp),
        }

        result = self.mt.order_send(request)
        if result is None:
            return {"retcode": None, "comment": "order_send returned None, error: " + str(mt5.last_error())}
        return result._asdict()

    def get_point(self):
        symbol_info = self.mt.symbol_info(self.symbol)
        point = symbol_info.point
        return point

    def info(self, timeframe, start_pos, count=60):
        tf = self.map_timeframe().get(timeframe)
        return self.getCandles(start_pos, count, tf).to_dict(orient="records")

    def timezone(self):
        # get latest tick
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            raise SystemExit("Could not get tick for " + self.symbol)

        server_ts = int(tick.time)  # server time in seconds
        utc_now_ts = int(datetime.utcnow().timestamp())

        # compute server offset
        offset_seconds = server_ts - utc_now_ts
        hours = offset_seconds / 3600
        print(f"Server time zone: UTC{hours:+.1f}")

    @staticmethod
    def safe_get(lst, index, default=None):
        try:
            return lst[index]
        except IndexError:
            return default

    def map_timeframe(self):
        return {
            "m1": self.mt.TIMEFRAME_M1,
            "m2": self.mt.TIMEFRAME_M2,
            "m3": self.mt.TIMEFRAME_M3,
            "m4": self.mt.TIMEFRAME_M4,
            "m5": self.mt.TIMEFRAME_M5,
            "m6": self.mt.TIMEFRAME_M6,
            "m10": self.mt.TIMEFRAME_M10,
            "m12": self.mt.TIMEFRAME_M12,
            "m15": self.mt.TIMEFRAME_M15,
            "m20": self.mt.TIMEFRAME_M20,
            "m30": self.mt.TIMEFRAME_M30,
            "1h": self.mt.TIMEFRAME_H1,
            "2h": self.mt.TIMEFRAME_H2,
            "4h": self.mt.TIMEFRAME_H4,
            "3h": self.mt.TIMEFRAME_H3,
            "6h": self.mt.TIMEFRAME_H6,
            "8h": self.mt.TIMEFRAME_H8,
            "12h": self.mt.TIMEFRAME_H12,
            "1d": self.mt.TIMEFRAME_D1,
            "1w": self.mt.TIMEFRAME_W1,
            "1mn": self.mt.TIMEFRAME_MN1,
        }

    def getCandles(self, start_pos, count, timeframe=None) -> pd.DataFrame:
        interval = timeframe
        candles = self.mt.copy_rates_from_pos(self.symbol, interval, start_pos, int(count))

        candles = pd.DataFrame(data=candles,
                               columns={
                                   'time': "datetime",
                                   'open': "open",
                                   'high': "high",
                                   'low': "low",
                                   'close': "close",
                                   'tick_volume': "tick_volume",
                                   'spread': "spread",
                               })
        candles['time'] = pd.to_datetime(candles['time'] - 2 * 60 * 60, unit='s')
        return candles
