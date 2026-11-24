# tests/test_logger.py
import logging
from src.utils.logger import SensitiveDataFilter


def test_sensitive_data_filter_masks_password():
    flt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg='User login attempt: {"username": 123456, "password": "SuperSecretPassword!"}',
        args=(),
        exc_info=None,
    )
    flt.filter(record)
    assert "SuperSecretPassword!" not in record.msg
    assert '***MASKED***' in record.msg


def test_sensitive_data_filter_masks_token():
    flt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg='Header check: token="my-api-secret-token"',
        args=(),
        exc_info=None,
    )
    flt.filter(record)
    assert "my-api-secret-token" not in record.msg
    assert '***MASKED***' in record.msg
