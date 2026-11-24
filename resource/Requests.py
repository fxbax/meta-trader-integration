# resource/Requests.py
# Backward-compatibility alias for src.schemas.payloads
from src.schemas.payloads import (
    Side,
    Platform,
    TypeTime,
    TypeFilling,
    Position,
    ClosePosition,
    ModifyPosition,
)

__all__ = [
    "Side",
    "Platform",
    "TypeTime",
    "TypeFilling",
    "Position",
    "ClosePosition",
    "ModifyPosition",
]
