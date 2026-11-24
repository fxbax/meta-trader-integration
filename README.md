# MetaTrader 5 Integration Service

A high-performance, production-ready Python service bridging web applications with the **MetaTrader 5 (MT5)** Windows terminal over a secure HTTP API.

---

## 1. Overview

This service provides an authenticated RESTful gateway to a locally running MetaTrader 5 terminal. It allows external applications to query real-time market rates, inspect account status, monitor open positions, retrieve historical trade deals, and execute trading actions (open, close, modify) with millisecond-level precision.

---

## 2. Key Features

- **Standard REST API**: Simple JSON endpoints for quotes, account data, trade execution, and position management.
- **Strict Backward Compatibility**: Preserves exact request/response shapes and status codes for existing consumers.
- **Production WSGI Server**: Powered by `Waitress`, providing multi-threaded concurrency on Windows Server.
- **Thread-Safe MT5 Session Management**: Prevents concurrent race conditions when issuing terminal commands.
- **Flexible Configuration**: Prioritized resolution across CLI arguments, environment variables, and configuration files.
- **Credential Protection**: Automatic masking of passwords and access tokens in logs.
- **Cross-Platform Testability**: Includes an extensive test suite with a complete MetaTrader 5 mock module.

---

## 3. Architecture Overview

```
External Application (e.g., Laravel / AI Signal Engine)
                        │  HTTP POST (Header: "token: <KEY>")
                        ▼
           ┌─────────────────────────┐
           │     Waitress WSGI       │
           └────────────┬────────────┘
                        │
           ┌────────────▼────────────┐
           │ Flask Routing & Auth     │
           │ Middleware (hmac-safe)   │
           └────────────┬────────────┘
                        │ Validated Schemas (Pydantic)
           ┌────────────▼────────────┐
           │     MT5Client Service   │  ◄── Thread Lock & Session Cache
           └────────────┬────────────┘
                        │ IPC / C-API
           ┌────────────▼────────────┐
           │ MetaTrader 5 Terminal   │
           │ (64-bit with AutoTrading│
           └─────────────────────────┘
```

---

## 4. Project Structure

```
.
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized configuration (Port, Token, Log Level)
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── middleware.py    # Timing-safe token authentication
│   │   └── routes.py        # 7 core API endpoints
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── payloads.py      # Pydantic request models & enums
│   ├── services/
│   │   ├── __init__.py
│   │   ├── exceptions.py    # Custom domain exceptions
│   │   └── mt5_client.py    # Thread-safe MT5 terminal wrapper
│   └── utils/
│       ├── __init__.py
│       └── logger.py        # Rotating file logger with credential masking
├── tests/
│   ├── conftest.py          # Pytest fixtures and complete MT5 mock
│   ├── test_api_contracts.py# Contract tests for all endpoints
│   ├── test_auth.py         # Authentication tests
│   ├── test_cli.py          # Command-line interface tests
│   ├── test_logger.py       # Sensitive data filter tests
│   ├── test_mt5_client.py   # MT5 service tests
│   └── test_settings.py     # Configuration tests
├── run.py                   # Production CLI & Service entry point
├── main.py                  # Backward-compatible application entry point
├── requirements.txt         # Production dependencies
├── .env.example             # Configuration template
├── CONTRIBUTING.md          # Developer contribution guide
└── LICENSE                  # MIT License
```

---

## 5. Requirements

- **Operating System**: Windows Server 2016+, Windows 10, or Windows 11 (64-bit).
- **Python**: Version 3.10 or higher (64-bit).
- **MetaTrader 5**: 64-bit desktop terminal installed and logged into a broker account.
- **Terminal Permissions**:
  - `AutoTrading` / `Algo Trading` toggled **ON** (green icon).
  - Terminal options (`Tools > Options > Expert Advisors`):
    - [x] Allow algorithmic trading
    - [x] Allow DLL imports

---

## 6. Installation

Clone the repository and install dependencies in a virtual environment:

```powershell
# Clone repository
git clone https://github.com/fxbax/meta-trader-integration.git
cd meta-trader-integration

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 7. Configuration

Create your local `.env` file from the example:

```powershell
copy .env.example .env
```

Open `.env` and configure your secret access token and desired port:

```env
PORT=5000
HOST=0.0.0.0
AUTH_TOKEN=your-random-secret-key-here
LOG_LEVEL=INFO
LOG_DIR=logs
```

---

## 8. Environment Variables

| Variable | Description | Default |
|---|---|---|
| `PORT` | TCP port the server binds to | `5000` |
| `HOST` | Network interface to bind to | `0.0.0.0` |
| `AUTH_TOKEN` | Required token in `token` HTTP header | *None (Required)* |
| `LOG_LEVEL` | Minimum logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `LOG_DIR` | Directory for rotating log files | `logs` |
| `SENTRY_DSN` | Remote error monitoring DSN (optional) | *Empty* |

---

## 9. Running the Application

### Production Mode (Recommended - Waitress WSGI)

```powershell
python run.py --port 5000 --threads 4
```

### Development Mode (with hot-reload)

```powershell
python run.py --dev --port 5000
```

### Overriding Settings via CLI

Command-line flags take precedence over `.env`:

```powershell
python run.py -p 8080 -t "custom-temporary-token" -l DEBUG
```

---

## 10. API Documentation

All requests must include the `token` header:

```http
token: your-random-secret-key-here
Content-Type: application/json
```

### 10.1. `POST /account-info`
Fetches balance, equity, leverage, and margin details.

**Request Body:**
```json
{
  "username": 123456,
  "password": "account_password",
  "server": "Broker-Server-Name"
}
```

**Success Response (`200 OK`):**
```json
{
  "login": 123456,
  "balance": 10000.0,
  "equity": 10000.0,
  "profit": 0.0,
  "leverage": 100,
  "margin": 0.0,
  "margin_free": 10000.0
}
```

---

### 10.2. `POST /positions`
Lists open positions, optionally filtered by symbol.

**Request Body:**
```json
{
  "username": 123456,
  "password": "account_password",
  "server": "Broker-Server-Name",
  "symbol": "EURUSD"
}
```

**Success Response (`200 OK`):**
```json
[
  {
    "ticket": 98765432,
    "symbol": "EURUSD",
    "type": 0,
    "volume": 0.1,
    "price_open": 1.05500,
    "sl": 1.05000,
    "tp": 1.06500,
    "profit": 15.20
  }
]
```

---

### 10.3. `POST /history`
Retrieves past deals within an optional date range.

**Request Body:**
```json
{
  "username": 123456,
  "password": "account_password",
  "server": "Broker-Server-Name",
  "from": "2026-01-01T00:00:00",
  "to": "2026-02-01T00:00:00"
}
```

---

### 10.4. `POST /trade`
Places a new market order.

**Request Body:**
```json
{
  "platform": "Metatrader",
  "server": "Broker-Server-Name",
  "username": "123456",
  "password": "account_password",
  "hedge": true,
  "symbol": "EURUSD",
  "side": "buy",
  "volume": 0.1,
  "sl": 1.05000,
  "tp": 1.06500,
  "comment": "ai-signal-101",
  "type_time": "gtc",
  "type_filling": "ioc"
}
```

---

### 10.5. `POST /close-position`
Closes an open position by its ticket.

**Request Body:**
```json
{
  "server": "Broker-Server-Name",
  "username": "123456",
  "password": "account_password",
  "ticket": 98765432,
  "comment": "close-signal"
}
```

---

### 10.6. `POST /modify-position`
Updates Stop Loss (SL) and Take Profit (TP) of an open position.

**Request Body:**
```json
{
  "server": "Broker-Server-Name",
  "username": "123456",
  "password": "account_password",
  "ticket": 98765432,
  "sl": 1.05200,
  "tp": 1.06800
}
```

---

### 10.7. `POST /info`
Queries multi-symbol and multi-timeframe candle data.

**Request Body:**
```json
{
  "username": "123456",
  "password": "account_password",
  "server": "Broker-Server-Name",
  "symbols": {
    "EURUSD": 60
  },
  "timeframes": {
    "m1": 0
  }
}
```

---

## 11. Error Handling & Status Codes

| Code | Meaning | Reason |
|---|---|---|
| `200` | OK | Request processed successfully. |
| `400` | Bad Request | Validation error in payload fields (via Pydantic). |
| `401` | Unauthorized | Missing or invalid `token` header. |
| `500` | Internal Server Error | Exception during trade execution or data processing. |
| `502` | Bad Gateway | Unable to connect to MT5 terminal or invalid broker credentials. |

---

## 12. Testing

The test suite runs on any operating system without requiring an active MT5 terminal:

```bash
pytest -v
```

All 38 test cases validate contract compliance, authentication rules, MT5 operations, and CLI parameters.

---

## 13. Windows Server Installation

For Windows Server environments without Python or developer tools:

### Option A: Graphical Windows Installer (`Setup.exe`)
1. Download `Setup-MetaTrader-Integration-v1.0.0.exe` from Releases.
2. Run the installer as Administrator.
3. In the setup wizard:
   - Select the target installation directory (default: `C:\Program Files\MetaTrader Integration`).
   - Specify your desired **HTTP API Port** (default: `5000`).
   - Specify your secret **Access Token (AUTH_TOKEN)**.
4. The installer automatically:
   - Extracts all runtime binaries and dependencies.
   - Creates the `.env` configuration file with your chosen Port and Token.
   - Registers an inbound Windows Firewall allow rule for the selected port.
   - Registers and starts the Windows Service with Automatic startup on server reboot.

### Option B: Standalone Extracted Package
If using the portable binary distribution:
```powershell
# In PowerShell as Administrator:
cd C:\MetaTrader-Integration\windows\service
.\install_service.ps1 -Port 5000 -AuthToken "your-secret-token"
```

---

## 14. Windows Service Management

The service runs continuously in the background as `MetaTraderIntegration`. Manage it via PowerShell or the Services MMC (`services.msc`):

```powershell
# Using the bundled management script
.\windows\service\manage_service.ps1 status
.\windows\service\manage_service.ps1 restart
.\windows\service\manage_service.ps1 logs

# Or using native Windows commands
net start MetaTraderIntegration
net stop MetaTraderIntegration
Restart-Service MetaTraderIntegration
```

### Changing Port or Access Key After Installation
Settings can be updated at any time without recompiling or reinstalling:
1. Open the `.env` file in the installation directory with Notepad.
2. Update `PORT=...` or `AUTH_TOKEN=...`.
3. If changing port, update the firewall: `netsh advfirewall firewall set rule name="MetaTrader Integration" new localport=<NEW_PORT>`.
4. Restart the service: `net stop MetaTraderIntegration && net start MetaTraderIntegration`.

---

## 15. Security Considerations

- **Authentication**: Token verification uses constant-time string comparison (`hmac.compare_digest`) to protect against timing attacks.
- **Credential Masking**: All logging handlers automatically redact `password` and `token` fields.
- **Firewall Restriction**: Restrict inbound access to the configured port (`PORT`) to trusted caller IP addresses.

---

## 16. Contributing

Contributions are welcome. Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for development workflows and guidelines.

---

## 17. License

Distributed under the [MIT License](LICENSE).
