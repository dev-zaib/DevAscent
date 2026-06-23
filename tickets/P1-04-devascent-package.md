# P1-04: Create `devascent/` Python Package

**Status:** ⬜ todo
**Phase:** 1 — Foundation
**Depends on:** P1-03
**Blocks:** P1-05, P2-01

## Goal
Create the `devascent/` Python package as the assessment engine layer. This follows Hermes's plugin architecture — assessment is a plugin/extension, not core modification.

## AC
- [ ] `devascent/` directory created with proper `__init__.py` files
- [ ] Package registered in `pyproject.toml` under `packages.find`
- [ ] `devascent/db/` module with SQLAlchemy async engine + session factory
- [ ] `devascent/db/models/` with base declarative model
- [ ] `devascent/config.py` with assessment-specific config loader
- [ ] `devascent/__init__.py` exports public API
- [ ] Package importable: `python -c "import devascent; from devascent.db import engine"`
- [ ] All files follow Hermes coding conventions (no bare open() without encoding on Windows paths)

## Directory Structure

```
devascent/
├── __init__.py              # Public API exports
├── config.py                # Assessment config (reads ~/.devascent/config.yaml)
├── db/
│   ├── __init__.py
│   ├── base.py              # AsyncEngine, async_session_maker, get_db()
│   └── models/
│       ├── __init__.py       # Import all models for Alembic
│       ├── base.py           # SQLAlchemy declarative Base
│       ├── user.py           # User model
│       ├── organization.py   # Org, OrgMember models
│       ├── cohort.py         # Cohort, CohortMember models
│       ├── challenge.py      # Challenge model (with pgvector column)
│       ├── assessment.py     # AssessmentSession, Submission models
│       ├── credential.py     # Credential model
│       └── audit.py          # AuditLog model
├── assessment/
│   └── __init__.py
├── rag/
│   └── __init__.py
├── queue/
│   └── __init__.py
├── api/
│   └── __init__.py
├── cert/
│   └── __init__.py
└── analytics/
    └── __init__.py
```

## `devascent/config.py` Implementation

```python
"""Assessment-specific configuration loader.

Follows Hermes convention: secrets in .env, settings in config.yaml.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from devascent_constants import get_devascent_home

load_dotenv(get_devascent_home() / ".env")

class AssessmentConfig:
    """Assessment configuration from environment + config.yaml."""
    
    @property
    def database_url(self) -> str:
        return os.getenv("DATABASE_URL", "postgresql+asyncpg://devascent:devascent@localhost:5432/devascent")
    
    @property
    def redis_url(self) -> str:
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    @property
    def openai_api_key(self) -> str | None:
        return os.getenv("OPENAI_API_KEY")
    
    @property
    def anthropic_api_key(self) -> str | None:
        return os.getenv("ANTHROPIC_API_KEY")
    
    @property
    def embedding_model(self) -> str:
        return os.getenv("DEVASCENT_EMBEDDING_MODEL", "text-embedding-3-small")

assessment_config = AssessmentConfig()
```

## `devascent/db/base.py` Implementation

```python
"""Database engine and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from devascent.config import assessment_config

engine = create_async_engine(
    assessment_config.database_url,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
```

## Hermes Convention Checks
- [x] Use `get_devascent_home()` not `Path.home() / ".devascent"` (profile-safe)
- [x] No HERMES_ env vars in new code — use DEVASCENT_ prefix
- [x] Secrets in `.env`, behavioral settings will go in `config.yaml` later
- [x] Module follows plugin pattern: self-contained, no core modifications