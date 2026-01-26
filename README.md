<div align="center">
 <h1>HoloHub</h1>
</div>
<div align="center">

**A Production-Grade Spatial Computing CMS for Managing Holographic Displays at Scale**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)

</div>

HoloHub is a comprehensive content management system designed specifically for managing holographic displays and spatial computing content. Built with modern technologies, it provides a complete solution for organizing, processing, and distributing 3D assets to fleets of holographic displays.

## Features

### Core Capabilities

- **Multi-Tenant Architecture** - Organization-based isolation with row-level security
- **3D Asset Management** - Upload, process, and manage GLB/GLTF files
- **Device Fleet Management** - Monitor and control holographic displays remotely
- **Playlist Scheduling** - Create content schedules with recurrence support
- **Real-Time Analytics** - Time-series data for device health and asset usage
- **Role-Based Access Control** - Granular permissions for team collaboration
- **Background Processing** - Async task queue for asset optimization
- **Web-Based 3D Preview** - Interactive preview of 3D models in the browser

### Technical Highlights

- **JWT Authentication** with access/refresh token rotation
- **MFA Support** (TOTP with backup codes)
- **TimescaleDB** for optimized time-series data storage
- **S3-Compatible Storage** (MinIO for development, AWS S3 for production)
- **React Three Fiber** for WebGL-based 3D visualization
- **Rate Limiting** and security best practices
- **SOC 2 Type II** compliance ready with audit logging

## Architecture

HoloHub follows a modern microservices-inspired architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  Next.js 14 + shadcn/ui + React Three Fiber               │
│  (http://localhost:3000)                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend API                         │
│  FastAPI + SQLAlchemy 2.0 + TimescaleDB                    │
│  (http://localhost:8000)                                    │
└───────────┬─────────────────────────────────────────────────┘
            │
    ┌───────┴────────┬────────────┬─────────────┐
    ▼                ▼            ▼             ▼
┌─────────┐    ┌──────────┐  ┌─────────┐  ┌──────────┐
│PostgreSQL│    │  Redis   │  │  MinIO  │  │  Celery  │
│+TimescaleDB   │  Cache/MQ│  │  S3     │  │  Worker  │
│ :5432    │    │  :6379   │  │ :9000   │  │  Flower  │
└─────────┘    └──────────┘  └─────────┘  │  :5555   │
                                          └──────────┘
```

## Project Structure

```
HoloHub/
├── frontend/                      # Next.js 14 admin dashboard
│   ├── app/                      # App Router pages
│   ├── components/               # React components
│   ├── lib/                      # Utilities, API client, stores
│   └── types/                    # TypeScript types
│
├── backend/                       # FastAPI backend
│   ├── app/
│   │   ├── api/                  # API endpoints
│   │   ├── core/                 # Security, config, RLS
│   │   ├── db/                   # Database session
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   └── tests/                # Pytest tests
│   ├── alembic/                  # Database migrations
│   └── docker/                   # Docker files
│
├── docs/                         # Documentation
│   └── holohub_tdd_v2.md         # Complete requirements
│
├── FRONTEND_PLAN.md              # Frontend implementation plan
└── README.md                     # This file
```

## Quick Start

### Prerequisites

- **Backend**: Python 3.12+, Poetry, Docker, Docker Compose
- **Frontend**: Node.js 18+, npm/yarn

### 1. Start the Backend

```bash
cd backend

# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start Docker services (PostgreSQL, Redis, MinIO)
docker-compose up -d

# Run database migrations
poetry run alembic upgrade head

# Start the API server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Adminer (DB GUI): http://localhost:8080
- Flower (Celery Monitor): http://localhost:5555

### 2. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with your settings

# Start the development server
npm run dev
```

The frontend will be available at:
- Frontend: http://localhost:3000

### 3. Create Your Account

1. Open http://localhost:3000 in your browser
2. Click "Sign up" and create your account
3. Your organization will be created automatically
4. Start uploading 3D assets and managing devices!

## Documentation

- **[Frontend README](frontend/README.md)** - Frontend setup and development
- **[Backend README](backend/README.md)** - Backend API documentation
- **[Frontend Implementation Plan](FRONTEND_PLAN.md)** - Detailed frontend architecture

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Technology Stack

### Backend

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 + TimescaleDB |
| Cache/MQ | Redis 7 |
| Storage | MinIO (S3-compatible) |
| Auth | JWT (python-jose) |
| MFA | pyotp (TOTP) |
| Tasks | Celery |
| Testing | pytest + Factory Boy |

### Frontend

| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| UI Library | shadcn/ui |
| Styling | Tailwind CSS |
| 3D Rendering | React Three Fiber |
| State Management | Zustand + TanStack Query |
| Forms | React Hook Form + Zod |
| HTTP Client | axios |

## Development

### Running Tests

**Backend:**
```bash
cd backend
poetry run pytest --cov=app --cov-report=html
```

**Frontend:**
```bash
cd frontend
npm run test
```

### Code Style

**Backend:**
```bash
poetry run black .     # Format
poetry run ruff check . # Lint
poetry run mypy .      # Type check
```

**Frontend:**
```bash
npm run format    # Format
npm run lint      # Lint
npm run type-check # Type check
```

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js application |
| API | 8000 | FastAPI backend |
| PostgreSQL | 5432 | Database with TimescaleDB |
| Redis | 6379 | Cache and message queue |
| MinIO | 9000, 9001 | S3-compatible storage |
| Adminer | 8080 | Database web GUI |
| Flower | 5555 | Celery task monitor |

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://holohub:password@localhost:5432/holohub

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=holohub-dev
```

### Frontend (.env.local)

```bash
# API
NEXT_PUBLIC_API_URL=http://localhost:8000

# S3/MinIO
NEXT_PUBLIC_S3_ENDPOINT=http://localhost:9000
NEXT_PUBLIC_S3_BUCKET=holohub-dev
```

## Deployment

### Backend Production

1. Use managed database (AWS RDS with TimescaleDB)
2. Configure ElastiCache Redis
3. Use AWS S3 for storage
4. Deploy to ECS/EKS or use Docker Swarm
5. Set up CloudFront CDN for assets
6. Enable monitoring with Prometheus/Grafana

### Frontend Production

1. Deploy to Vercel (recommended)
2. Configure environment variables
3. Set up custom domain
4. Enable Vercel Analytics
5. Configure CORS for production API

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [License](License) file for details.

## Support

For questions, issues, or suggestions:
- Open an issue on GitHub
- Check the [documentation docs/holohub_tdd_v2.md](docs/holohub_tdd_v2.md)
- Review the API docs at http://localhost:8000/docs

---

**Built with ❤️ for the spatial computing community**
