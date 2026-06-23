# Phase 3-9: Remaining Feature Tickets

> **Concise tickets for phases 3-9. See BOARD.md for status tracking.**

---

## Phase 3 — RAG Pipeline

### P3-01: pgvector + Challenge Table
Create `challenges` table with `embedding vector(1536)`, HNSW index. Run migration.

### P3-02: Embedding Generation Service
`devascent/rag/embedder.py` — `generate_embedding(text) -> list[float]` using OpenAI `text-embedding-3-small`. Rate-limited, cached.

### P3-03: Seed Enterprise Challenges
`devascent/rag/seed_data.py` — 16 challenges from spec, each with title, description, rubric JSONB, target_skills array, target_level, hints. Auto-embed on insert.

### P3-04: ChallengeRetriever
`devascent/rag/retriever.py` — `retrieve_challenge(user_id, weak_skills) -> Challenge`. pgvector cosine similarity query, dedup against user's completed challenges, fallback to un-attempted.

### P3-05: User Weak Spot Embeddings
Generate embedding from user's lowest-3 skill scores. Store in `user_weak_spots` table. Trigger on every `UpdateSkillsMatrix` run.

### P3-06: Integrate Retriever
Wire `ChallengeRetriever.retrieve_challenge()` into `PresentChallenge` LangGraph node.

---

## Phase 4 — Sandbox Executor

### P4-01: gVisor Sandbox Docker Image
`docker/Dockerfile.sandbox` — Ubuntu base + Node 22 + Python 3.11 + Go 1.22 + Rust. `runsc` runtime installed. Image tagged `devascent-sandbox:latest`.

### P4-02: SandboxExecutor
`devascent/assessment/evaluator/sandbox.py` — extends Hermes `tools/environments/docker.py` pattern. `execute(code, language) -> (stdout, stderr, exit_code)`. Docker API with gVisor runtime, tmpfs, no network, seccomp, 30s timeout, 512MB memory, 1 CPU.

### P4-03: Seccomp Profile + Limits
`devascent/assessment/evaluator/seccomp.json` — allow only: read, write, exit, sigreturn, mmap, brk, mprotect, munmap, fstat, close, arch_prctl. All other syscalls → ERRNO.

### P4-04: Constraint Validator
`devascent/assessment/evaluator/constraint_validator.py` — after escalation, scan solution code for required patterns (Redis usage, circuit breaker, virtualization). Missing constraint → -15pt penalty.

### P4-05: Rate Limiter
`devascent/api/middleware/rate_limit.py` — Redis sliding window, 10 submissions/user/hour. FastAPI middleware.

---

## Phase 5 — BullMQ + SSE

### P5-01: BullMQ + ioredis
`npm install bullmq ioredis` in `web/`. Create `web/src/lib/queue.ts` — queue connection, job types.

### P5-02: Evaluation Worker
`web/worker/evaluation.worker.ts` — BullMQ worker picks up job, spawns `python -m devascent.assessment.run --job-id X` subprocess, emits events to Redis pub/sub.

### P5-03: SSE Endpoint
`devascent/api/routes/stream.py` — `GET /api/assessment/stream/:jobId` using `sse-starlette`. Listens on Redis pub/sub channel for job events, streams to client.

### P5-04: SSE Client Hook
`web/src/hooks/useSSE.ts` — EventSource wrapper with reconnect (exponential backoff), buffer management, typed event parsing.

### P5-05: POST /submit → 202
`devascent/api/routes/assessment.py` — `POST /api/assessment/:id/submit` → enqueue BullMQ job → return 202 with `{ jobId, streamUrl }`.

---

## Phase 6 — Go Harder Escalation

### P6-01: EscalateChallenge Node
`devascent/assessment/nodes/escalate.py` — LangGraph node. Checks escalation depth, applies mutation prompt.

### P6-02: Escalation Prompt Template
Jinja2 template with depth-aware constraint selection. Depth 1: scale/latency/data. Depth 2: fault/partition/exhaustion. Depth 3: security/failover/migration.

### P6-03: Constraint Catalog
YAML catalog of constraint types per depth level, with detection patterns for constraint validator.

### P6-04: Escalation Cap + LevelAdvance
Escalation depth capped at 3. When cap hit → route to `LevelAdvance` node. Level transitions: BASELINE → SYSTEM_DESIGNER → TOP_1_PERCENT → ARCHITECT.

---

## Phase 7 — Stitch UI + Onboarding

### P7-01: Stitch MCP Design System
Google Stitch MCP: create design system with Geist Sans + Inter, dark mode, ROUND_EIGHT, #0a0a0a / #fafafa palette. Apply to assessment workspace screens.

### P7-02: ChallengePanel
`web/src/components/assessment/ChallengePanel.tsx` — react-markdown renderer, collapsible sections, copy-to-clipboard, fullscreen toggle.

### P7-03: CodeReviewStream
`web/src/components/assessment/CodeReviewStream.tsx` — SSE-connected, react-syntax-highlighter, @tanstack/react-virtual for terminal logs.

### P7-04: SkillsRadarMap + SkillBarMeter
SVG-based radar chart (6-8 axes, animated), horizontal bar stack (0-100, color-coded green/yellow/red).

### P7-05: LevelBadge + EscalationGauge
Animated badge with level transitions, escalation depth gauge (0-3 with intensity).

### P7-06: SubmissionHistory
Virtualized list of past attempts with score + timestamp + expandable detail.

### P7-07: OnboardingWizard
6-step flow: welcome → self-assessment (8 sliders) → benchmark challenge → calibration → workspace tour → first challenge.

### P7-08: Assessment Workspace Page
`web/src/pages/assess/[sessionId].tsx` — 3-panel layout, responsive, wire all components.

---

## Phase 8 — Enterprise

### P8-01: NextAuth.js
Credentials + GitHub + Google OAuth providers. Session persistence in PostgreSQL.

### P8-02: RBAC Middleware
`devascent/api/middleware/auth.py` — JWT verification, role check (`candidate`, `reviewer`, `org_admin`, `platform_admin`).

### P8-03: Org + Cohort CRUD
Full CRUD for organizations, members, cohorts. Multi-tenant data isolation.

### P8-04: Org Dashboard
Heatmap across cohort, individual progress tracker, CSV/PDF export, audit log viewer.

### P8-05: W3C VC Credentials
Ed25519 keypair, JSON-LD credential issuance, public verifier page, revocation list.

### P8-06: GitHub CI/CD Integration
GitHub App with PR comment trigger (`/devascent-assess`), Check Run results, webhook API.

---

## Phase 9 — Observability + Launch

### P9-01: Prometheus + Grafana
`/metrics` endpoint, queue depth/latency/error gauges. Grafana dashboards for system + business.

### P9-02: OpenTelemetry
Spans: API request → queue enqueue → worker process → sandbox exec → LLM call → DB write. Pino structured logging with request ID propagation.

### P9-03: k6 Load Tests
1000 concurrent: submit assessment, SSE stream saturation, session state polling.

### P9-04: Docker Compose Assessment
`docker-compose.assessment.yml` — postgres + redis + web + worker + sandbox provisioner.

### P9-05: Railway Deploy
`railway.toml` — 3 web replicas, 3 workers, managed PG + Redis. Health checks, restart policy.

### P9-06: Security Audit
Dependency scan (npm audit, pip-audit), secret detection, gVisor escape test, rate limit bypass test.

### P9-07: Documentation
OpenAPI docs (auto from FastAPI), deployment guide, user onboarding guide.