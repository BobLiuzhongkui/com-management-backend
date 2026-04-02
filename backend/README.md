# Com Management Backend

FastAPI + SQLAlchemy async REST API for multi-tenant communication management.

---

## Architecture

```
backend/
├── app/
│   ├── main.py                  # Application factory + lifespan
│   ├── core/
│   │   ├── config.py            # Pydantic-settings (env-driven)
│   │   ├── database.py          # Async SQLAlchemy engine + session
│   │   ├── logging.py           # structlog configuration
│   │   └── security.py          # JWT helpers + bcrypt password hashing
│   ├── models/
│   │   ├── tenant.py            # Tenant, ComConfig, TenantStatus
│   │   └── user.py              # User (auth)
│   ├── schemas/
│   │   ├── tenant.py            # TenantCreate / TenantUpdate / TenantResponse
│   │   ├── auth.py              # LoginRequest / RefreshTokenRequest / TokenResponse
│   │   └── user.py              # UserCreate / UserResponse
│   ├── repositories/
│   │   ├── tenant.py            # Async CRUD for Tenant
│   │   └── user.py              # Async CRUD for User
│   ├── services/
│   │   ├── tenant.py            # Business logic: tenant lifecycle
│   │   └── auth.py              # Business logic: login, refresh, user creation
│   ├── api/
│   │   ├── deps.py              # FastAPI dependency providers + auth guards
│   │   └── v1/
│   │       ├── router.py        # Aggregates all v1 sub-routers
│   │       └── endpoints/
│   │           ├── tenants/     # GET/POST/PUT/DELETE /tenants
│   │           └── auth/        # POST /auth/login|refresh|logout, GET /auth/me
│   ├── middleware/
│   │   └── logging.py           # Request-ID injection + structured request logs
│   └── adapters/
│       └── base.py              # Abstract interfaces for comm providers (Twilio etc.)
├── alembic/                     # Database migrations
│   └── versions/
│       └── 0001_initial_schema.py
├── tests/
│   ├── conftest.py              # Fixtures: in-memory SQLite, test client, users
│   ├── test_health.py
│   ├── test_auth.py
│   └── test_tenants.py
├── requirements.txt
├── pytest.ini
└── alembic.ini
```

### Request flow

```
Client
  → CORSMiddleware
  → RequestLoggingMiddleware   (attaches X-Request-ID, structured logs)
  → FastAPI router
  → Endpoint function
  → Service (business logic, raises ValueError on domain errors)
  → Repository (async SQLAlchemy, no raw SQL outside of SELECT/COUNT)
  → PostgreSQL (asyncpg driver)
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | ≥ 3.11 |
| PostgreSQL | ≥ 14 |
| Redis | ≥ 7 (optional — Celery workers) |

---

## Local development

### 1. Clone and install

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set POSTGRES_PASSWORD and SECRET_KEY
```

Minimum `.env` for local development:

```env
ENVIRONMENT=development
POSTGRES_SERVER=localhost
POSTGRES_USER=comadmin
POSTGRES_PASSWORD=comadmin
POSTGRES_DB=com_management
SECRET_KEY=dev-secret-key-change-me-in-prod-32ch
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: http://localhost:8000/api/v1/docs

---

## Environment variables reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development` / `staging` / `production` |
| `POSTGRES_SERVER` | `localhost` | DB host |
| `POSTGRES_PORT` | `5432` | DB port |
| `POSTGRES_USER` | `comadmin` | DB user |
| `POSTGRES_PASSWORD` | `comadmin` | DB password |
| `POSTGRES_DB` | `com_management` | Database name |
| `SQLALCHEMY_DATABASE_URI` | *(auto-assembled)* | Override full async URI |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_URL` | *(auto-assembled)* | Override full Redis URI |
| `SECRET_KEY` | *(required)* | JWT signing key (≥ 32 chars in non-dev) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `console` | `console` (dev) or `json` (prod) |

---

## API overview

All routes are prefixed with `/api/v1`.

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/login` | — | Email + password → JWT pair |
| `POST` | `/auth/refresh` | — | Refresh token → new JWT pair |
| `POST` | `/auth/logout` | Bearer | Invalidate session (client-side) |
| `GET` | `/auth/me` | Bearer | Current user profile |

### Tenants

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/tenants/` | Bearer | List tenants (paginated) |
| `GET` | `/tenants/search?q=` | Bearer | Search by name |
| `GET` | `/tenants/{id}` | Bearer | Get single tenant |
| `POST` | `/tenants/` | Bearer | Create tenant |
| `PUT` | `/tenants/{id}` | Bearer | Update tenant |
| `DELETE` | `/tenants/{id}` | Superuser | Delete tenant |

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health check |

---

## Running tests

Tests use an in-memory SQLite database — no PostgreSQL required.

```bash
cd backend
pytest                       # all tests
pytest -v tests/test_auth.py # single file
pytest --cov=app             # with coverage report
```

---

## Database migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# Auto-generate a new migration after model changes
alembic revision --autogenerate -m "describe your change"
```

---

## Deployment (production checklist)

- [ ] Set `ENVIRONMENT=production`
- [ ] Set a strong `SECRET_KEY` (≥ 32 random characters)
- [ ] Use a managed PostgreSQL instance (RDS, Cloud SQL, etc.)
- [ ] Set `LOG_FORMAT=json` for log aggregation (Datadog, CloudWatch, etc.)
- [ ] Run behind a reverse proxy (nginx / ALB) that enforces TLS
- [ ] Run `alembic upgrade head` in a pre-deploy hook / init container
- [ ] Set `BACKEND_CORS_ORIGINS` to your actual frontend domain(s)
- [ ] Configure Redis for Celery task workers (if using background jobs)

### Docker (example)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## Extending the adapters

Implement `CommProviderAdapter` from `app/adapters/base.py` to add a new
communication provider (Twilio, Plivo, Vonage, etc.):

```python
from app.adapters.base import CommProviderAdapter

class TwilioAdapter(CommProviderAdapter):
    async def connect(self): ...
    async def disconnect(self): ...
    async def send_sms(self, to, body): ...
    async def send_email(self, to, subject, body): ...
    async def get_status(self, message_id): ...
```
