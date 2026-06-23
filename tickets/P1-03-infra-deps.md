# P1-03: Add Infrastructure Dependencies

**Status:** ⬜ todo
**Phase:** 1 — Foundation
**Depends on:** P1-02
**Blocks:** P1-04, P1-05

## Goal
Add PostgreSQL, Redis, and assessment-specific Python dependencies to the project. Follow Hermes's strict pinning policy (exact pins for core, `>=floor,<next_major` for extras).

## AC
- [ ] `pyproject.toml`: assessment deps added with pins
- [ ] `package.json`: BullMQ, ioredis, NextAuth added
- [ ] `.env.example`: `DATABASE_URL`, `REDIS_URL` added
- [ ] `docker-compose.yml`: PostgreSQL 18 + pgvector, Redis 7 services added
- [ ] `uv lock` regenerated with all new deps
- [ ] `npm install` succeeds in `web/` workspace

## Python Deps to Add (pyproject.toml core)

Per Hermes policy — exact `==X.Y.Z` pins for always-used packages:

```toml
dependencies = [
  # ... existing Hermes deps ...

  # Assessment engine
  "langgraph==0.4.18",                    # State machine
  "langgraph-checkpoint-postgres==3.0.1", # PG state persistence
  "psycopg[binary]==3.2.9",              # PostgreSQL driver (replaces asyncpg — psycopg3 is LangGraph's preferred)
  "pgvector==0.4.3",                      # Vector extension
  "alembic==1.16.4",                      # Database migrations
  
  # Redis
  "redis[hiredis]==6.1.0",                # Redis client + C parser
  
  # API
  "sse-starlette==2.3.5",                 # Server-Sent Events
  "python-jose[cryptography]==3.4.0",     # JWT (already in Hermes as PyJWT, but python-jose is more complete)
  
  # Observability  
  "prometheus-client==0.22.1",            # Metrics export
]
```

## Python Deps to Add (pyproject.toml extras)

```toml
[project.optional-dependencies]
assessment = [
  "sqlalchemy[asyncio]==2.0.44",          # ORM (for models outside LangGraph)
  "opentelemetry-api==1.33.0",            # Tracing API
  "opentelemetry-sdk==1.33.0",            # Tracing SDK
  "opentelemetry-instrumentation-fastapi==0.54b0",
]
dev = [
  # ... existing dev deps ...
  "pytest-asyncio==1.3.0",               # Already present
  "httpx==0.28.1",                        # Already present — use for API testing
]
```

## TypeScript Deps to Add (web/package.json)

```bash
cd web
npm install bullmq ioredis next-auth@beta @auth/core zod zustand
npm install -D @types/ioredis
```

## Docker Compose Additions

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg18-trixie
    environment:
      POSTGRES_USER: devascent
      POSTGRES_PASSWORD: devascent
      POSTGRES_DB: devascent
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

## Hermes Convention Checks
- [x] Exact `==X.Y.Z` pins for core deps (always loaded)
- [x] `>=floor,<next_major` for optional extras
- [x] No new `DEVASCENT_*` env vars for non-secret config — timeout/threshold settings go in `config.yaml`
- [x] `DATABASE_URL` and `REDIS_URL` are secrets (contain credentials) — allowed in `.env`