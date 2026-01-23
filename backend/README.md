# HoloHub Backend API

Production-grade FastAPI backend for HoloHub - a spatial computing CMS for managing holographic displays at scale.

## Features

- **Multi-tenant architecture** with organization-based row-level security
- **JWT authentication** with access/refresh token pattern and MFA support
- **Time-series data** using TimescaleDB for device heartbeats and analytics
- **Async/await** throughout for optimal performance
- **Docker Compose** stack for local development
- **Comprehensive testing** with pytest and Factory Boy

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.12+ | Runtime environment |
| **FastAPI** | ^0.115.0 | Modern async web framework |
| **SQLAlchemy** | ^2.0.35 | Async ORM with relationship management |
| **PostgreSQL** | 16+ | Primary database |
| **TimescaleDB** | Latest | Time-series extension for PostgreSQL |
| **Redis** | 7-alpine | Caching and message queue |
| **Alembic** | ^1.13.2 | Database version control |
| **Celery** | ^5.4.0 | Background task processing |
| **MinIO** | Latest | S3-compatible object storage |
| **python-jose** | ^3.3.0 | JWT token creation/validation |
| **passlib** | ^1.7.4 | Secure password hashing (bcrypt) |
| **pyotp** | Latest | TOTP-based MFA |
| **SlowAPI** | ^0.1.9 | Request rate limiting |
| **pytest** | ^8.3.3 | Testing framework |
| **Factory Boy** | ^3.3.1 | Test data generation |

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   │
│   ├── core/                        # Core utilities
│   │   ├── config.py                # Pydantic settings (lru cached)
│   │   ├── security.py              # JWT, password hashing, MFA, device auth
│   │   └── row_level_security.py    # RLS helpers, RBAC, permissions
│   │
│   ├── db/                          # Database
│   │   ├── base.py                  # SQLAlchemy engine, session factory
│   │   └── redis.py                 # Redis manager
│   │
│   ├── models/                      # SQLAlchemy models
│   │   ├── organization.py          # Organization with tier/billing
│   │   ├── user.py                  # User with roles, MFA, lockout
│   │   ├── device.py                # Device + DeviceHeartbeat (TimescaleDB)
│   │   ├── asset.py                 # Asset + AssetAnalytics (TimescaleDB)
│   │   ├── playlist.py              # Playlist + PlaylistItem + DevicePlaylist
│   │   └── audit_log.py             # Compliance logging (SOC 2)
│   │
│   ├── schemas/                     # Pydantic schemas
│   │   ├── common.py                # Base schemas, pagination
│   │   ├── token.py                 # JWT token schemas
│   │   ├── organization.py          # Organization CRUD schemas
│   │   ├── user.py                  # User CRUD, auth schemas
│   │   ├── device.py                # Device CRUD, heartbeat schemas
│   │   ├── asset.py                 # Asset CRUD, upload schemas
│   │   └── playlist.py              # Playlist CRUD, scheduling schemas
│   │
│   ├── api/                         # API endpoints
│   │   ├── deps.py                  # Dependency injection (auth, pagination, RLS)
│   │   └── v1/
│   │       ├── router.py            # API router aggregation
│   │       ├── auth.py              # Auth endpoints (login, register, MFA)
│   │       ├── organizations.py     # Organization CRUD
│   │       ├── users.py             # User CRUD
│   │       ├── devices.py           # Device CRUD + commands
│   │       ├── assets.py            # Asset CRUD + upload
│   │       └── playlists.py         # Playlist CRUD + scheduling
│   │
│   └── tests/
│       ├── conftest.py              # Pytest fixtures (DB, client, factories)
│       ├── factories/
│       │   ├── __init__.py
│       │   ├── organization.py      # OrganizationFactory
│       │   ├── user.py              # UserFactory
│       │   ├── device.py            # DeviceFactory (with ActiveDeviceFactory)
│       │   ├── asset.py             # AssetFactory (with CompletedAssetFactory)
│       │   └── playlist.py          # PlaylistFactory (with items)
│       └── test_api/
│           └── test_auth.py         # Auth endpoint tests
│
├── alembic/                         # Database migrations
│   ├── versions/                    # Migration files
│   ├── env.py                       # Alembic environment config
│   └── script.py.mako               # Migration template
│
├── docker/                          # Docker files
│   └── Dockerfile.api               # Multi-stage build for API
│
├── postman/                         # API collections
│   └── HoloHub_API.postman_collection.json
│
├── alembic.ini                      # Alembic configuration
├── docker-compose.yml               # Full stack orchestration
├── pyproject.toml                   # Poetry dependencies
├── .env.example                     # Environment variables template
├── pytest.ini                       # Pytest configuration
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Poetry
- Docker and Docker Compose
- PostgreSQL 16 (or use Docker)

### Installation

1. **Clone the repository**
   ```bash
   cd HoloHub/backend
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

5. **Run database migrations**
   ```bash
   poetry run alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Documentation (Swagger): http://localhost:8000/docs
   - Documentation (ReDoc): http://localhost:8000/redoc
   - Adminer (DB GUI): http://localhost:8080

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | FastAPI application |
| PostgreSQL | 5432 | Database with TimescaleDB |
| Redis | 6379 | Cache and message queue |
| MinIO | 9000, 9001 | S3-compatible storage (API + Console) |
| Adminer | 8080 | Database web GUI |
| Flower | 5555 | Celery task monitor |
| Worker | - | Celery background worker |

## Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Application
APP_NAME=HoloHub
APP_ENV=development
DEBUG=true
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql+asyncpg://holohub:password@localhost:5432/holohub
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
MFA_ENCRYPTION_KEY=change-me-in-production

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=holohub-dev
S3_REGION=us-east-1
S3_USE_SSL=false

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URI=redis://localhost:6379/1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3

# Logging
LOG_LEVEL=INFO
```

## Database Models

### Organization
- Multi-tenant support with tier (free/pro/enterprise)
- Storage quotas and device limits
- Billing integration (Stripe customer ID)
- Branding customization (JSONB)

### User
- Role-based access control (owner/admin/editor/viewer)
- MFA support with TOTP and backup codes
- Account lockout after failed login attempts
- Password expiration and force reset

### Device
- Hardware authentication with device secrets (Argon2id)
- Status tracking (pending/active/offline/maintenance/decommissioned)
- Display configuration (resolution, orientation, quilt format)
- Network info (IP, MAC, WiFi SSID)
- TimescaleDB hypertable for heartbeats with health metrics

### Asset
- Processing pipeline status (pending → processing → completed/failed)
- Geometry stats (polygons, vertices, textures, materials, animations)
- Multiple output formats (GLB, Draco, Quilts, Video, Thumbnail)
- SHA-256 hash for deduplication
- CDN URLs (JSONB)
- TimescaleDB hypertable for analytics

### Playlist
- Scheduling with recurrence rules (daily/weekly/monthly)
- Transition types (cut/fade/dissolve/wipe)
- Device assignment with priority
- Shuffle and loop modes
- Timezone support

### Audit Log
- SOC 2 Type II compliance
- Tracks all mutations with before/after values
- Action type categorization
- Organization-scoped

## API Endpoints

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user + org |
| POST | `/login` | Get access + refresh tokens |
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Invalidate refresh token |
| GET | `/me` | Get current user with org |
| POST | `/mfa/setup` | Generate TOTP secret |
| POST | `/mfa/verify` | Enable MFA |
| POST | `/mfa/disable` | Disable MFA |
| POST | `/password/reset-request` | Request reset email |
| POST | `/password/reset` | Reset password with token |
| POST | `/token` | OAuth2 compatible (for Swagger) |

### Organizations (`/api/v1/organizations`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/current` | Get current organization |
| PATCH | `/current` | Update organization |
| GET | `/current/stats` | Get org statistics |
| GET | `/current/usage` | Get storage/billing usage |

### Users (`/api/v1/users`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List users in org |
| POST | `/invite` | Invite new user |
| GET | `/{id}` | Get user |
| PATCH | `/{id}` | Update user |
| DELETE | `/{id}` | Delete user |
| POST | `/me/password` | Change password |

### Devices (`/api/v1/devices`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List devices |
| POST | `/` | Register device |
| GET | `/{id}` | Get device |
| PATCH | `/{id}` | Update device |
| DELETE | `/{id}` | Delete device |
| POST | `/{id}/command` | Send command (restart, clear_cache, screenshot) |
| GET | `/{id}/health` | Get health metrics (TimescaleDB) |
| GET | `/{id}/logs` | Get device logs |
| GET | `/{id}/playlists` | Get assigned playlists |

### Assets (`/api/v1/assets`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List assets |
| POST | `/upload/request` | Request presigned upload URL |
| POST | `/upload/confirm` | Confirm upload and create asset |
| GET | `/{id}` | Get asset |
| PATCH | `/{id}` | Update asset |
| DELETE | `/{id}` | Delete asset |
| POST | `/{id}/reprocess` | Reprocess asset |
| GET | `/{id}/analytics` | Get analytics (TimescaleDB) |

### Playlists (`/api/v1/playlists`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List playlists |
| POST | `/` | Create playlist |
| GET | `/{id}` | Get playlist with items |
| PATCH | `/{id}` | Update playlist |
| DELETE | `/{id}` | Delete playlist |
| POST | `/{id}/items` | Add item |
| PATCH | `/{id}/items/{item_id}` | Update item |
| DELETE | `/{id}/items/{item_id}` | Remove item |
| POST | `/{id}/items/reorder` | Reorder items |
| POST | `/{id}/assign` | Assign to devices |
| POST | `/{id}/unassign` | Unassign from devices |

## Row-Level Security

HoloHub implements organization-based multi-tenancy:

1. **All queries filter by `organization_id`** from authenticated user
2. **RBAC with role hierarchy**: owner > admin > editor > viewer
3. **Granular permissions** for specific actions
4. **SQLAlchemy session context** for RLS

```python
# Applied automatically via dependencies
def get_current_organization() -> Organization:
    return current_user.organization

# Queries automatically filter
query = select(Device).where(Device.organization_id == org_id)
```

## Authentication Flow

```
1. User registers → Creates Organization + User (owner role)
2. User logs in with email/password
3. Server validates credentials (bcrypt verify)
4. If MFA enabled, prompt for TOTP code
5. Server returns:
   - access_token (JWT, 15min expiry)
   - refresh_token (JWT, 7 days expiry, stored in DB)
6. Client includes access_token in Authorization: Bearer header
7. When access_token expires, client calls /refresh
8. Server validates refresh_token, issues new access_token
```

## Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest app/tests/test_api/test_auth.py

# Run with verbose output
poetry run pytest -v
```

### Test Fixtures

```python
# Available in conftest.py
def test_user()  # Authenticated user
def test_organization()  # Test organization
def test_organization_pro()  # Pro tier organization
def test_device()  # Test device
def test_asset()  # Test asset
def test_playlist()  # Test playlist

# Factory Boy
from app.tests.factories import UserFactory, DeviceFactory, AssetFactory
user = UserFactory(email="test@example.com")
device = DeviceFactory(status=DeviceStatus.ACTIVE)
asset = AssetFactory(processing_status=ProcessingStatus.COMPLETED)
```

## Postman Collection

1. Import `postman/HoloHub_API.postman_collection.json` into Postman
2. Set the `base_url` variable to `http://localhost:8000`
3. Run requests in the "Authentication" folder to register and login
4. Tokens will be automatically stored in variables for subsequent requests

## Background Tasks (Celery)

```bash
# Start Celery worker
poetry run celery -A app.worker worker --loglevel=info --concurrency=4

# Start Flower (monitor)
poetry run celery -A app.worker flower --port=5555
```

### Available Tasks
- `process_asset`: Process uploaded 3D models
- `generate_quilt`: Generate quilt outputs for Looking Glass
- `compress_draco`: Apply Draco compression
- `create_thumbnail`: Generate asset thumbnails
- `transcode_video`: Transcode to video format

## Development

### Code Style

The project uses:
- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type check
poetry run mypy .
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install
```

## Deployment

### Production Considerations

1. **Change secret keys** - Use `openssl rand -hex 32`
2. **Set `APP_ENV=production`**
3. **Use managed database** (AWS RDS, Aurora with TimescaleDB)
4. **Configure CloudFront** for CDN (asset delivery)
5. **Enable Sentry** for error tracking
6. **Set up monitoring** with Prometheus/Grafana
7. **Use HTTPS** with valid certificates
8. **Configure backup strategy** for PostgreSQL

### Build Docker Image

```bash
docker build -f docker/Dockerfile.api -t holohub-api .
```

### Run in Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## License

MIT License - see LICENSE file for details.
