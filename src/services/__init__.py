# src/services/__init__.py
from .mt5_client import MT5Client
from .exceptions import (
    MT5Error,
    MT5ConnectionError,
    MT5PositionNotFoundError,
    MT5TickError,
)

# Backward-compatible alias
Metatrader = MT5Client

__all__ = [
    "MT5Client",
    "Metatrader",
    "MT5Error",
    "MT5ConnectionError",
    "MT5PositionNotFoundError",
    "MT5TickError",
]
