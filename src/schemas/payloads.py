# src/schemas/payloads.py
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Side(str, Enum):
    sell = 'sell'
    buy = 'buy'


class Platform(str, Enum):
    Metatrader = 'Metatrader'
    Fxcm = 'Fxcm'


class TypeTime(str, Enum):
    gtc = 'gtc'
    day = 'day'


class TypeFilling(str, Enum):
    fok = 'fok'
    ioc = 'ioc'
    return_ = 'return'


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
    type_time: TypeTime = TypeTime.gtc
    type_filling: TypeFilling = TypeFilling.ioc


class ClosePosition(BaseModel):
    server: str
    username: str
    password: str
    ticket: int
    comment: Optional[str] = None


class ModifyPosition(BaseModel):
    server: str
    username: str
    password: str
    ticket: int
    sl: Optional[float] = None
    tp: Optional[float] = None
