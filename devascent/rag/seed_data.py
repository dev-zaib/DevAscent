"""16 enterprise-grade engineering challenge scenarios.

Each challenge includes:
- title, description, difficulty, target_skills, target_level
- rubric (scoring dimensions with weights)
- hints (progressive hint system)
- solution_checklist (must-have items)

Topics cover: async flows, connection pooling, rate limiting,
memory management, caching, scraping, concurrency, messaging,
idempotency, resilience, API design, auth, distributed systems,
WebSocket backpressure, multi-tenancy, graceful shutdown.
"""

SEED_CHALLENGES = [
    {
        "title": "Redis-Backed Rate Limiter Under Load",
        "description": (
            "Build a TypeScript rate limiter middleware for an Express API. "
            "Limit requests to 100 per minute per API key. Use Redis for "
            "distributed state. Handle Redis connection failures gracefully "
            "by falling back to an in-memory LRU cache. Add a sliding window "
            "algorithm that prevents boundary burst attacks. Return proper "
            "429 Too Many Requests with Retry-After and X-RateLimit-* headers."
        ),
        "difficulty": "intermediate",
        "target_skills": ["rate_limiting", "redis", "fault_tolerance", "api_design"],
        "target_level": "SYSTEM_DESIGNER",
        "rubric": {
            "rate_limiting": {"weight": 30, "description": "Correct sliding window algorithm"},
            "redis": {"weight": 25, "description": "Proper Redis usage with fallback"},
            "fault_tolerance": {"weight": 25, "description": "Graceful degradation on Redis failure"},
            "api_design": {"weight": 20, "description": "Clean middleware interface + RFC headers"},
        },
        "hints": [
            "Use sorted sets in Redis with ZREMRANGEBYSCORE for window cleanup",
            "The sliding window prevents the burst issue that fixed windows have",
        ],
        "solution_checklist": [
            "Sliding window rate limiting per API key",
            "Redis connection with reconnect + fallback",
            "In-memory LRU cache fallback",
            "429 with Retry-After header",
            "X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers",
        ],
    },
    {
        "title": "Database Connection Pool Exhaustion Debug",
        "description": (
            "A production Node.js service is experiencing intermittent 500 errors "
            "under moderate load. The PostgreSQL connection pool (pg-pool, max 20) "
            "is being exhausted. Diagnose the root cause and rewrite the data access "
            "layer to prevent connection leaks. Implement: connection timeout monitoring, "
            "pool wait-time metrics, query timeout enforcement, and a health check "
            "endpoint that reports pool stats. The service handles 200 req/s."
        ),
        "difficulty": "intermediate",
        "target_skills": ["connection_pooling", "postgres", "debugging", "monitoring"],
        "target_level": "SYSTEM_DESIGNER",
        "rubric": {
            "connection_pooling": {"weight": 40, "description": "Correct pool sizing and leak prevention"},
            "postgres": {"weight": 30, "description": "Proper query lifecycle management"},
            "debugging": {"weight": 15, "description": "Root cause identification approach"},
            "monitoring": {"weight": 15, "description": "Pool metrics and health endpoint"},
        },
        "hints": [
            "Check if connections are being released after transactions",
            "pg-pool's idleTimeoutMillis and max are your primary tuning knobs",
        ],
        "solution_checklist": [
            "Identified connection leak source",
            "Proper try/finally for connection release",
            "Query timeout (statement_timeout)",
            "Pool metrics endpoint (/health/pool)",
            "Connection wait-time monitoring",
        ],
    },
    {
        "title": "Memory Leak in Long-Running Worker",
        "description": (
            "A Node.js background worker processes CSV files (up to 500MB each) "
            "and inserts rows into PostgreSQL. After processing ~20 files, the "
            "worker OOM-kills at 512MB heap. Profile the memory usage, identify "
            "the leak, and rewrite using streaming. Use Node.js streams or async "
            "iterators to process rows one at a time. Add heap snapshots at configurable "
            "intervals. Implement backpressure handling if the DB is slower than CSV reads."
        ),
        "difficulty": "hard",
        "target_skills": ["memory_management", "streaming", "profiling", "backpressure"],
        "target_level": "TOP_1_PERCENT",
        "rubric": {
            "memory_management": {"weight": 35, "description": "No unbounded memory growth"},
            "streaming": {"weight": 30, "description": "Proper Node.js streaming pipeline"},
            "profiling": {"weight": 20, "description": "Memory profiling and monitoring"},
            "backpressure": {"weight": 15, "description": "Handles slow DB writes"},
        },
        "hints": [
            "csv-parse supports streaming mode — use pipeline()",
            "A Transform stream that batches inserts can improve throughput",
        ],
        "solution_checklist": [
            "Streaming CSV parse (not readFileSync + split)",
            "Constant memory usage regardless of file size",
            "Heap snapshot at configurable intervals",
            "Backpressure from Writable to DB insert",
            "Processes 500MB file without OOM",
        ],
    },
    {
        "title": "Distributed Rate-Limited API Gateway",
        "description": (
            "Design an API gateway that enforces per-tenant rate limits across "
            "multiple gateway instances. A tenant is allowed 1000 req/s globally, "
            "not per instance. Use Redis for coordination. The gateway must be "
            "stateless and horizontally scalable. Implement token bucket algorithm "
            "with Redis Lua scripts for atomicity. Handle the case where a Redis "
            "shard is unavailable — the gateway must not block all traffic."
        ),
        "difficulty": "hard",
        "target_skills": ["rate_limiting", "redis", "distributed_systems", "fault_tolerance"],
        "target_level": "TOP_1_PERCENT",
        "rubric": {
            "distributed_systems": {"weight": 35, "description": "Correct distributed coordination"},
            "rate_limiting": {"weight": 30, "description": "Token bucket with atomic Lua"},
            "redis": {"weight": 20, "description": "Redis Lua script for rate limiting"},
            "fault_tolerance": {"weight": 15, "description": "Graceful Redis failure handling"},
        },
        "hints": [
            "EVAL the Lua script atomically — don't do GET + INCR separately",
            "Consider using Redis Cluster for high availability",
        ],
        "solution_checklist": [
            "Token bucket algorithm in Redis Lua",
            "Global rate limit across instances",
            "Stateless gateway design",
            "Graceful degradation on Redis failure",
            "Configurable per-tenant limits",
        ],
    },
    {
        "title": "Row Virtualization for 50k-Record Data Grid",
        "description": (
            "Build a React data grid component that renders 50,000 records without "
            "UI lag. Implement window-based virtualization — only render rows "
            "currently in the viewport plus a small overscan buffer. Support: "
            "variable row heights, column sorting, multi-select with Shift+Click, "
            "and inline cell editing. The grid must maintain 60fps during scroll "
            "with real data from an async data source (simulated)."
        ),
        "difficulty": "intermediate",
        "target_skills": ["rendering", "performance", "react", "data_structures"],
        "target_level": "SYSTEM_DESIGNER",
        "rubric": {
            "performance": {"weight": 40, "description": "60fps scroll with 50k rows"},
            "rendering": {"weight": 30, "description": "Correct virtualization implementation"},
            "react": {"weight": 15, "description": "Clean React patterns (hooks, memo)"},
            "data_structures": {"weight": 15, "description": "Efficient data access patterns"},
        },
        "hints": [
            "Calculate visible range from scrollTop / rowHeight",
            "Use absolute positioning for rows inside a spacer div",
        ],
        "solution_checklist": [
            "Window-based row virtualization",
            "Only visible + overscan rows in DOM",
            "Variable row height support",
            "Sort on column click",
            "Shift+Click multi-select",
            "Inline cell editing",
            "Smooth 60fps scroll",
        ],
    },
    {
        "title": "Headless Browser Pool for Web Scraping",
        "description": (
            "Build a web scraping service using a pool of Playwright browsers. "
            "Manage browser lifecycle: launch, reuse, health-check, and cleanup. "
            "Implement concurrent scraping with a configurable pool size. Handle: "
            "browser crashes (auto-restart), memory leaks (periodic restart after "
            "N pages), CAPTCHA detection (report to caller), and request queuing "
            "with priority. Must support at least 10 concurrent scrapes."
        ),
        "difficulty": "hard",
        "target_skills": ["scraping", "concurrency", "resource_management", "fault_tolerance"],
        "target_level": "TOP_1_PERCENT",
        "rubric": {
            "resource_management": {"weight": 30, "description": "Proper browser pool lifecycle"},
            "concurrency": {"weight": 30, "description": "Efficient concurrent scraping"},
            "scraping": {"weight": 25, "description": "Correct Playwright usage"},
            "fault_tolerance": {"weight": 15, "description": "Crash recovery + memory management"},
        },
        "hints": [
            "Use Playwright's browserType.launch() with a pool wrapper",
            "Track page count per browser — restart after threshold",
        ],
        "solution_checklist": [
            "Browser pool with configurable size",
            "Concurrent scraping (max N browsers)",
            "Auto-restart crashed browsers",
            "Memory leak prevention (restart after N pages)",
            "CAPTCHA detection + reporting",
            "Priority-based request queue",
        ],
    },
    {
        "title": "Event-Driven Dead Letter Queue System",
        "description": (
            "Implement a dead letter queue (DLQ) system for an event-driven "
            "microservice. Events that fail processing after 3 retries go to the DLQ. "
            "The DLQ must: persist events to PostgreSQL, support replay (move back "
            "to main queue), support inspection (browse by type, time range), "
            "and alert if DLQ depth exceeds threshold. Use RabbitMQ or Redis streams "
            "as the message broker."
        ),
        "difficulty": "intermediate",
        "target_skills": ["messaging", "fault_tolerance", "postgres", "system_design"],
        "target_level": "SYSTEM_DESIGNER",
        "rubric": {
            "messaging": {"weight": 30, "description": "Correct DLQ pattern implementation"},
            "fault_tolerance": {"weight": 30, "description": "Retry logic + failure handling"},
            "postgres": {"weight": 20, "description": "Event persistence schema"},
            "system_design": {"weight": 20, "description": "Replay + inspection + alerting design"},
        },
        "hints": [
            "Each event needs: id, type, payload, retry_count, last_error, created_at",
            "Use exponential backoff between retries",
        ],
        "solution_checklist": [
            "3 retries with exponential backoff",
            "DLQ persistence to PostgreSQL",
            "Replay from DLQ to main queue",
            "Browse DLQ by type and time range",
            "Alert on DLQ depth > threshold",
        ],
    },
    {
        "title": "Idempotent Payment Processing",
        "description": (
            "Design an idempotent payment processing endpoint. Clients send a "
            "payment request with an idempotency key. If the same key is received "
            "again, return the cached result instead of processing a duplicate. "
            "Handle: concurrent requests with the same key (return same result), "
            "key expiration (24h TTL in Redis), and partial failures (the payment "
            "provider timed out but might have succeeded). Use PostgreSQL for "
            "durable storage and Redis for fast lookups."
        ),
        "difficulty": "hard",
        "target_skills": ["idempotency", "transactions", "redis", "postgres"],
        "target_level": "TOP_1_PERCENT",
        "rubric": {
            "idempotency": {"weight": 40, "description": "Correct idempotency key handling"},
            "transactions": {"weight": 25, "description": "Atomic payment + result storage"},
            "redis": {"weight": 20, "description": "Fast key lookup with TTL"},
            "postgres": {"weight": 15, "description": "Durable key-result storage"},
        },
        "hints": [
            "Use Redis SET NX for locking concurrent requests on same key",
            "Store results in PostgreSQL with the idempotency key as unique constraint",
        ],
        "solution_checklist": [
            "Idempotency key handling (same key → same result)",
            "Concurrent request dedup (lock or transaction)",
            "24h key TTL in Redis",
            "Durable storage in PostgreSQL",
            "Partial failure handling (payment timeout edge case)",
        ],
    },
    {
        "title": "Circuit Breaker for Flaky External Dependency",
        "description": (
            "Implement a circuit breaker for an HTTP client calling a flaky "
            "external service. The circuit breaker must: track failure rate "
            "over a sliding window, open the circuit when failure rate > 50%, "
            "enter half-open state after a cooldown period, and allow a probe "
            "request before fully closing. Expose metrics: circuit state, "
            "failure count, success count, last transition timestamp."
        ),
        "difficulty": "intermediate",
        "target_skills": ["resilience", "patterns", "monitoring", "http"],
        "target_level": "SYSTEM_DESIGNER",
        "rubric": {
            "resilience": {"weight": 40, "description": "Correct circuit breaker states"},
            "patterns": {"weight": 30, "description": "Clean implementation of the pattern"},
            "monitoring": {"weight": 20, "description": "Metrics exposure"},
            "http": {"weight": 10, "description": "Proper HTTP client integration"},
        },
        "hints": [
            "Circuit states: CLOSED → OPEN (threshold exceeded) → HALF_OPEN (after cooldown) → CLOSED",
            "Use a sliding time window, not a fixed counter, for failure rate",
        ],
        "solution_checklist": [
            "Three states: CLOSED, OPEN, HALF_OPEN",
            "Sliding window failure rate tracking",
            "Configurable threshold and cooldown",
            "HALF_OPEN probe request logic",
            "Prometheus-compatible metrics",
        ],
    },
    {
        "title": "Cursor-Based API Pagination",
        "description": (
            "Design a paginated REST API endpoint that lists resources using "
            "cursor-based pagination (not offset-based). Return: items array, "
            "next_cursor (opaque string), has_more boolean. The cursor must be "
            "opaque to clients and stable under data insertions. Handle: empty "
            "results, maximum page size enforcement, cursor tampering detection. "
            "Back the API with PostgreSQL using keyset pagination on indexed columns."
        ),
        "difficulty": "easy",
        "target_skills": ["api_design", "postgres", "data_structures"],
        "target_level": "BASELINE",
        "rubric": {
            "api_design": {"weight": 40, "description": "Clean cursor-based pagination"},
            "postgres": {"weight": 40, "description": "Efficient keyset pagination query"},
            "data_structures": {"weight": 20, "description": "Opaque cursor encoding"},
        },
        "hints": [
            "Encode the last seen ID + created_at as a base64 cursor",
            "WHERE (created_at, id) > ($1, $2) ORDER BY created_at, id LIMIT $3",
        ],
        "solution_checklist": [
            "Cursor-based (not offset-based) pagination",
            "Opaque cursor encoding (base64 or similar)",
            "Keyset pagination query on indexed columns",
            "Stable under concurrent insertions",
            "Cursor tampering detection",
            "Max page size enforcement",
        ],
    },
    {
        "title": "JWT Rotation with Refresh Token Blacklisting",
        "description": (
            "Implement a JWT authentication system with access token rotation "
            "and refresh token blacklisting. Access tokens expire in 15 minutes, "
            "refresh tokens in 7 days. On refresh: issue new access + refresh tokens, "
            "blacklist the old refresh token in Redis. Detect refresh token reuse "
            "(replay attack) — if a blacklisted token is used, blacklist ALL tokens "
            "for that user (forced re-login). Use RS256 asymmetric signing."
        ),
        "difficulty": "hard",
        "target_skills": ["auth", "security", "redis", "api_design"],
        "target_level": "TOP_1_PERCENT",
        "rubric": {
            "auth": {"weight": 35, "description": "Correct JWT + refresh token flow"},
            "security": {"weight": 35, "description": "Replay detection + blacklisting"},
            "redis": {"weight": 15, "description": "Token blacklist in Redis"},
            "api_design": {"weight": 15, "description": "Clean auth endpoint design"},
        },
        "hints": [
            "Store refresh token hash in Redis, not the raw token",
            "On refresh: issue new pair, add old refresh hash to blacklist with TTL",
        ],
        "solution_checklist": [
            "Access token: 15min, RS256 signed",
            "Refresh token: 7 days, opaque",
            "Token rotation on refresh",
            "Refresh token blacklist (Redis, TTL-aligned)",
            "Replay detection → force re-login",
            "Refresh token family tracking",
        ],
    },
    {
        "title": "Redlock Distributed Lock for Cron Jobs",
        "description": (
            "Implement a distributed lock using the Redlock algorithm for cron "
            "job coordination. Multiple instances of a service run scheduled jobs. "
            "Only one instance should execute each job. Use Redis (at least 3 "
            "instances for Redlock quorum). Handle: lock expiration (job runs longer "
            "than TTL), clock drift between instances, and Redis instance failure "
            "during lock acquisition. Implement a fencing token to prevent split-brain."
        ),
        "difficulty": "hard",
        "target_skills": ["distributed_systems", "redis", "concurrency", "fault_tolerance"],
        "target_level": "TOP_1_PERCENT",
        "rubric": {
            "distributed_systems": {"weight": 40, "description": "Correct Redlock implementation"},
            "redis": {"weight": 25, "description": "Multi-instance Redis lock logic"},
            "concurrency": {"weight": 20, "description": "Lock + fencing token for safety"},
            "fault_tolerance": {"weight": 15, "description": "Redis failure handling"},
        },
        "hints": [
            "Acquire: SET NX PX on N/2+1 instances within timeout",
            "Release: check value match, then DEL — use Lua for atomicity",
        ],
        "solution_checklist": [
            "Redlock algorithm with >= 3 Redis instances",
            "Quorum-based lock acquisition",
            "Lock expiration with TTL",
            "Fencing token for split-brain prevention",
            "Atomic lock release (Lua script)",
            "Clock drift tolerance",
        ],
    },
    {
        "title": "WebSocket Fan-Out With Backpressure",
        "description": (
            "Build a WebSocket server that fans out messages to N connected "
            "clients. When a message arrives on a Redis pub/sub channel, broadcast "
            "it to all subscribed WebSocket clients. Handle backpressure: if a "
            "client's send buffer is full (slow consumer), drop the client after "
            "a grace period. Implement: connection heartbeat (ping/pong), "
            "per-client message queue with bounded size, graceful degradation "
            "when Redis pub/sub is unavailable. Support 10k concurrent connections."
        ),
        "difficulty": "hard",
        "target_skills": ["realtime", "backpressure", "redis", "scaling"],
        "target_level": "TOP_1_PERCENT",
        "rubric": {
            "realtime": {"weight": 30, "description": "Correct WebSocket fan-out"},
            "backpressure": {"weight": 30, "description": "Slow consumer handling"},
            "redis": {"weight": 20, "description": "Pub/sub integration"},
            "scaling": {"weight": 20, "description": "10k connection scalability design"},
        },
        "hints": [
            "ws.bufferedAmount tells you how much data is queued",
            "Use a per-client ring buffer with configurable max size",
        ],
        "solution_checklist": [
            "WebSocket server with Redis pub/sub fan-out",
            "Backpressure detection (bufferedAmount threshold)",
            "Per-client bounded message queue",
            "Slow consumer disconnect with grace period",
            "Heartbeat (ping/pong every 30s)",
            "10k connection design (not necessarily full implementation)",
        ],
    },
    {
        "title": "Multi-Tenant RLS Policy Design",
        "description": (
            "Design a PostgreSQL Row-Level Security (RLS) policy system for a "
            "multi-tenant SaaS application. Each tenant's data must be completely "
            "isolated. Implement: RLS policies that enforce tenant_id filtering, "
            "a middleware layer that sets the tenant context per request, bypass "
            "RLS for admin queries with audit logging, and a tenant data export "
            "endpoint. The schema includes: users, projects, tasks — all multi-tenant."
        ),
        "difficulty": "intermediate",
        "target_skills": ["multi_tenancy", "security", "postgres", "api_design"],
        "target_level": "SYSTEM_DESIGNER",
        "rubric": {
            "multi_tenancy": {"weight": 35, "description": "Correct tenant isolation"},
            "security": {"weight": 30, "description": "RLS policy design + bypass safety"},
            "postgres": {"weight": 25, "description": "RLS + app_user + tenant context"},
            "api_design": {"weight": 10, "description": "Export + admin endpoints"},
        },
        "hints": [
            "SET app.current_tenant_id = '...' in a transaction-local setting",
            "CREATE POLICY tenant_isolation ON projects FOR ALL USING (tenant_id = current_setting('app.current_tenant_id')::uuid)",
        ],
        "solution_checklist": [
            "RLS policies on all multi-tenant tables",
            "Transaction-local tenant context (SET LOCAL)",
            "Admin bypass with audit logging",
            "Tenant data export endpoint",
            "No tenant can access another tenant's data",
        ],
    },
    {
        "title": "Semantic Caching Layer for LLM Responses",
        "description": (
            "Build a semantic caching layer that reduces LLM API costs. When a "
            "user query arrives, check if a semantically similar query has been "
            "cached. Use embeddings + cosine similarity to determine similarity. "
            "Cache hits must have similarity >= 0.95 to be returned. Store: "
            "query embedding, response, timestamp, hit count. Implement cache "
            "invalidation: max age TTL, max entries (LRU eviction). Use pgvector "
            "for embedding storage and similarity search."
        ),
        "difficulty": "intermediate",
        "target_skills": ["caching", "embeddings", "postgres", "system_design"],
        "target_level": "SYSTEM_DESIGNER",
        "rubric": {
            "caching": {"weight": 30, "description": "Correct semantic cache design"},
            "embeddings": {"weight": 30, "description": "Embedding similarity search"},
            "postgres": {"weight": 25, "description": "pgvector index + query"},
            "system_design": {"weight": 15, "description": "TTL + LRU eviction logic"},
        },
        "hints": [
            "Use pgvector's <=> operator for cosine distance",
            "Post-filter: only return results where 1 - distance >= 0.95",
        ],
        "solution_checklist": [
            "Embedding generation for incoming queries",
            "pgvector similarity search (cosine distance)",
            "0.95 similarity threshold",
            "Max age TTL for cache entries",
            "LRU eviction when cache is full",
            "Cache hit/miss ratio metrics",
        ],
    },
    {
        "title": "Graceful Shutdown for Containerized Service",
        "description": (
            "Implement graceful shutdown for a Dockerized Node.js HTTP service. "
            "On SIGTERM: stop accepting new connections, wait for in-flight "
            "requests to complete (max 30s), close database connections, flush "
            "logs, and exit. If requests don't complete within timeout, force "
            "exit. Add: a /health endpoint that returns 503 during shutdown to "
            "signal the load balancer to drain. Implement a preStop hook in "
            "Kubernetes that calls a drain endpoint 10s before SIGTERM."
        ),
        "difficulty": "easy",
        "target_skills": ["deployment", "signal_handling", "kubernetes", "node_js"],
        "target_level": "BASELINE",
        "rubric": {
            "deployment": {"weight": 30, "description": "Correct graceful shutdown flow"},
            "signal_handling": {"weight": 30, "description": "SIGTERM handling + timeout"},
            "kubernetes": {"weight": 20, "description": "preStop hook + readiness probe"},
            "node_js": {"weight": 20, "description": "Clean resource cleanup pattern"},
        },
        "hints": [
            "server.close() stops accepting connections but doesn't close existing ones",
            "Use a flag: let isShuttingDown = false; set on SIGTERM",
        ],
        "solution_checklist": [
            "SIGTERM handler",
            "Stop accepting new connections",
            "30s grace period for in-flight requests",
            "Force exit after timeout",
            "/health returns 503 during shutdown",
            "Kubernetes preStop hook",
            "Database connection cleanup",
        ],
    },
]
