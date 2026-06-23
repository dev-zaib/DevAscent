# P1-05: PostgreSQL Data Model + Alembic Migrations

**Status:** ⬜ todo | **Depends on:** P1-04 | **Blocks:** P2-05, P3-01

## AC
- [ ] All SQLAlchemy models defined in `devascent/db/models/`
- [ ] pgvector column on `challenges.embedding` with HNSW index
- [ ] Alembic initialized with async template
- [ ] Initial migration creates all tables + extensions (uuid-ossp, vector)
- [ ] Seed migration creates 16 enterprise challenges with embeddings
- [ ] Models match the spec from DEVASCENT_STORIES.md exactly

## Models (same schema as DEVASCENT_STORIES.md)
`users`, `organizations`, `org_members`, `cohorts`, `cohort_members`, `challenges`, `assessment_sessions`, `submissions`, `user_weak_spots`, `audit_logs`, `credentials`

## Alembic Setup
```bash
cd repo
alembic init -t async devascent/db/migrations
# Configure alembic.ini → devascent/db/alembic.ini
# env.py → use devascent.db.base.engine
```

## Key Detail
- `challenges.embedding` uses `Vector(1536)` from pgvector
- HNSW index: `CREATE INDEX ON challenges USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);`
- All UUID PKs via `uuid_generate_v4()`
- Timestamps via `server_default=func.now()`