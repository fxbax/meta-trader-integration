from enum import Enum
from pydantic import BaseModel
from typing import Optional


class Side(str, Enum):
    sell = 'sell'
    buy = 'buy'


class Platform(str, Enum):
    Metatrader = 'Metatrader'
    Fxcm = 'Fxcm'


# order_send()'s "type_time" (order validity) — deliberately only the two
# values that never require an "expiration" date (SPECIFIED/SPECIFIED_DAY
# are not supported, to avoid adding an expiration field end-to-end).
class TypeTime(str, Enum):
    gtc = 'gtc'
    day = 'day'


# order_send()'s "type_filling" — the three values relevant to forex/CFD
# retail brokers (BOC is exchange-only and not offered).
# NOTE: member name is `return_`, not `return` — `return` is a reserved
# Python keyword. The wire *value* is still the plain string 'return'.
class TypeFilling(str, Enum):
    fok = 'fok'
    ioc = 'ioc'
    return_ = 'return'


# One order per request — matches the app's real AI trade-signal shape
# (Laravel's `forex_signal` prompt: side/volume/sl/tp are single values, not
# per-leg lists). There is deliberately no "hold" side here: Laravel filters
# a "hold" signal out before ever calling this endpoint, since there is no
# corresponding MT5 order to place for it.
class Position(BaseModel):
    platform: Platform
    server: str
    username: str
    password: str
    hedge: bool
    symbol: str
    side: Side
    volume: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: Optional[str] = None
    # Defaults mirror the values these fields replace (previously hardcoded
    # in service/Metatrader/main.py as ORDER_TIME_GTC / ORDER_FILLING_IOC),
    # so an older Laravel deploy that doesn't send these keys yet still
    # trades exactly like before this change.
    type_time: TypeTime = TypeTime.gtc
    type_filling: TypeFilling = TypeFilling.ioc


# Close an open position by its MT5 ticket (from POST /positions) — used by
# Laravel's trade-review flow when the AI decides the position should exit at
# market now.
class ClosePosition(BaseModel):
    server: str
    username: str
    password: str
    ticket: int
    comment: Optional[str] = None


# Change the SL/TP of an open position (TRADE_ACTION_SLTP). An omitted/null
# level keeps the position's current value — it does NOT remove the level
# (sending 0.0 to MT5 would).
class ModifyPosition(BaseModel):
    server: str
    username: str
    password: str
    ticket: int
    sl: Optional[float] = None
    tp: Optional[float] = None
