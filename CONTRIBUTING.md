# Contributing to MetaTrader 5 Integration

Thank you for your interest in contributing to this project. This service acts as an HTTP bridge between external systems and the MetaTrader 5 Windows terminal.

## Development Guidelines

1. **Strict Backward Compatibility**:
   - The HTTP API contract (routes, request shapes, response fields, error codes) is consumed by active production systems. No breaking changes to existing endpoints are permitted.

2. **Code Structure**:
   - `src/api/`: HTTP route handlers and authentication middleware.
   - `src/schemas/`: Pydantic models for incoming payload validation.
   - `src/services/`: MT5 client and connection lifecycle manager.
   - `config/`: Application settings and environment resolution.
   - `tests/`: Automated test suite with MetaTrader 5 mock.

3. **Running Tests**:
   - All tests use an in-memory mock of the MetaTrader 5 C-library, allowing execution on any operating system (Windows, Linux, macOS).
   ```bash
   pytest -v
   ```

4. **Code Quality**:
   - Adhere to PEP 8 standards.
   - Use explicit imports (avoid `from module import *`).
   - Ensure all credentials and sensitive tokens are masked in logs.
