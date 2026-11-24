# src/services/exceptions.py

class MT5Error(Exception):
    """Base exception for all MT5 operations."""
    pass


class MT5ConnectionError(MT5Error):
    """Raised when connection or login to MT5 fails."""
    pass


class MT5PositionNotFoundError(MT5Error):
    """Raised when a position ticket is not found."""
    pass


class MT5TickError(MT5Error):
    """Raised when tick data cannot be retrieved for a symbol."""
    pass
