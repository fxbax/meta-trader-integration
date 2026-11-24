# src/services/mt5_client.py
import threading
from typing import Optional, Any, Dict, List
import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

from src.services.exceptions import MT5ConnectionError
from src.utils.logger import logger


class MT5Client:
    """Thread-safe client wrapping MetaTrader5 API operations."""

    _lock = threading.RLock()
    _active_session: Optional[tuple] = None  # (account_id, server)

    def __init__(
        self,
        symbol: Optional[str] = None,
        username: Optional[Any] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        path: Optional[str] = None,
    ) -> None:
        if mt5 is None:
            raise RuntimeError(
                "MetaTrader5 package is not available on this platform. "
                "MetaTrader 5 integration requires Windows and the MetaTrader5 Python package."
            )
        self.mt = mt5
        self.symbol = symbol

        if username is not None:
            self.connect(
                login=int(username),
                password=password,
                server=server,
                path=path,
            )

    def connect(
        self,
        login: int,
        password: Optional[str] = None,
        server: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Any:
        account = int(login)

        with self._lock:
            # Check if current active session matches requested credentials
            if (
                self._active_session == (account, server)
                and self.mt.account_info() is not None
            ):
                return self.mt

            self.mt.initialize(server=server, login=account, password=password)
            authorized = self.mt.login(
                login=account, server=server, password=password, path=path
            )

            if authorized:
                self._active_session = (account, server)
                logger.info(f"Connected to MT5 account #{account} on {server}")
                return self.mt
            else:
                last_err = self.mt.last_error()
                logger.error(f"Failed to connect at account #{account}, error code: {last_err}")
                self.mt.shutdown()
                self._active_session = None
                raise MT5ConnectionError(f"Failed to connect at account #{account}, error: {last_err}")

    def set_symbol(self, symbol: str) -> "MT5Client":
        self.symbol = symbol
        return self

    def get_account_info(self) -> Optional[Any]:
        with self._lock:
            return self.mt.account_info()

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            positions = (
                self.mt.positions_get(symbol=symbol)
                if symbol
                else self.mt.positions_get()
            )
            if positions is None:
                return []
            return [position._asdict() for position in positions]

    def get_history(self, date_from: Any, date_to: Any) -> List[Dict[str, Any]]:
        with self._lock:
            deals = self.mt.history_deals_get(date_from, date_to)
            if deals is None:
                return []
            return [deal._asdict() for deal in deals]

    def _order_time_constant(self, value: Any) -> int:
        mapping = {
            "gtc": self.mt.ORDER_TIME_GTC,
            "day": self.mt.ORDER_TIME_DAY,
        }
        val_str = getattr(value, "value", value)
        return mapping.get(val_str, self.mt.ORDER_TIME_GTC)

    def _order_filling_constant(self, value: Any) -> int:
        mapping = {
            "fok": self.mt.ORDER_FILLING_FOK,
            "ioc": self.mt.ORDER_FILLING_IOC,
            "return": self.mt.ORDER_FILLING_RETURN,
        }
        val_str = getattr(value, "value", value)
        return mapping.get(val_str, self.mt.ORDER_FILLING_IOC)

    def trade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
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
                return {
                    "retcode": None,
                    "comment": "order_send returned None, error: " + str(self.mt.last_error()),
                }
            return result._asdict()

    def _find_position(self, ticket: Any) -> Any:
        positions = self.mt.positions_get(ticket=int(ticket))
        if not positions:
            raise Exception("No open position with ticket " + str(ticket))
        return positions[0]

    def close_position(self, ticket: Any, comment: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
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
                return {
                    "retcode": None,
                    "comment": "order_send returned None, error: " + str(self.mt.last_error()),
                }
            return result._asdict()

    def modify_position(
        self, ticket: Any, sl: Optional[float] = None, tp: Optional[float] = None
    ) -> Dict[str, Any]:
        with self._lock:
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
                return {
                    "retcode": None,
                    "comment": "order_send returned None, error: " + str(self.mt.last_error()),
                }
            return result._asdict()

    def get_candles(self, start_pos: int, count: int, timeframe: Optional[int] = None) -> pd.DataFrame:
        with self._lock:
            interval = timeframe
            candles = self.mt.copy_rates_from_pos(self.symbol, interval, start_pos, int(count))

            candles_df = pd.DataFrame(data=candles)
            if not candles_df.empty and "time" in candles_df.columns:
                candles_df["time"] = pd.to_datetime(candles_df["time"] - 2 * 60 * 60, unit="s")
            return candles_df

    # Backward-compatible method name alias
    getCandles = get_candles

    def info(self, timeframe: str, start_pos: int, count: int = 60) -> List[Dict[str, Any]]:
        tf = self.map_timeframe().get(timeframe)
        return self.get_candles(start_pos, count, tf).to_dict(orient="records")

    def map_timeframe(self) -> Dict[str, int]:
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
