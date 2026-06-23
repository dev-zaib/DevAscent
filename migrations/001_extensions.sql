-- DevAscent: Initial PostgreSQL bootstrap
-- Auto-executed by Docker on first startup (docker-entrypoint-initdb.d)

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
