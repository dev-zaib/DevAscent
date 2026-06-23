# DevAscent — Ticket Tracking Board

> **Repo:** `git@github.com-dev-zaib:dev-zaib/DevAscent.git`
> **Base:** Forked from `NousResearch/hermes-agent` (MIT, v0.17.0)
> **Last updated:** 2026-06-23

| Status Key |
|-----------|
| ⬜ `todo` · 🟦 `in_progress` · ✅ `done` · ❌ `blocked` · 🔵 `review` |

---

## Phase 1: Fork & Foundation (Week 1)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P1-01 | Strip unused gateway platforms + tools | ⬜ | — | — |
| P1-02 | Rename `hermes` → `devascent` across codebase | ⬜ | — | — |
| P1-03 | Add PostgreSQL + Redis + assessment deps | ⬜ | — | — |
| P1-04 | Create `devascent/` Python package | ⬜ | — | — |
| P1-05 | Define PostgreSQL data models + Alembic | ⬜ | — | — |
| P1-06 | OpenAPI spec for assessment API | ⬜ | — | — |

## Phase 2: LangGraph State Machine (Week 2)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P2-01 | `DevAscentState` typed dict + Pydantic validation | ⬜ | — | — |
| P2-02 | LangGraph state graph with PG checkpointer | ⬜ | — | — |
| P2-03 | `InitializeAssessment` node | ⬜ | — | — |
| P2-04 | `PresentChallenge` node | ⬜ | — | — |
| P2-05 | `EvaluateSubmission` node + rubric engine | ⬜ | — | — |
| P2-06 | `UpdateSkillsMatrix` node | ⬜ | — | — |
| P2-07 | `DetermineNextStep` router + conditional edges | ⬜ | — | — |
| P2-08 | Assessment API endpoints (FastAPI) | ⬜ | — | — |

## Phase 3: RAG Pipeline (Week 3)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P3-01 | pgvector extension + challenge table | ⬜ | — | — |
| P3-02 | Embedding generation service | ⬜ | — | — |
| P3-03 | Seed 16 enterprise challenges | ⬜ | — | — |
| P3-04 | `ChallengeRetriever` similarity search | ⬜ | — | — |
| P3-05 | User weak spot embedding generator | ⬜ | — | — |
| P3-06 | Integrate retriever into `PresentChallenge` | ⬜ | — | — |

## Phase 4: Sandbox Executor (Week 4)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P4-01 | gVisor sandbox Docker image | ⬜ | — | — |
| P4-02 | `SandboxExecutor` (extends Hermes `docker.py`) | ⬜ | — | — |
| P4-03 | Seccomp profile + resource limits | ⬜ | — | — |
| P4-04 | Constraint validator (post-escalation checks) | ⬜ | — | — |
| P4-05 | Rate limiter (Redis sliding window) | ⬜ | — | — |

## Phase 5: BullMQ + SSE (Week 5)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P5-01 | BullMQ + ioredis in web package | ⬜ | — | — |
| P5-02 | Evaluation worker (TS → Python subprocess) | ⬜ | — | — |
| P5-03 | SSE endpoint + `sse-starlette` | ⬜ | — | — |
| P5-04 | SSE client hook (`useSSE`) | ⬜ | — | — |
| P5-05 | `POST /submit` → 202 + stream URL | ⬜ | — | — |

## Phase 6: Go Harder Escalation (Week 6)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P6-01 | `EscalateChallenge` LangGraph node | ⬜ | — | — |
| P6-02 | Escalation prompt template (depth-aware) | ⬜ | — | — |
| P6-03 | Constraint catalog (depth 1-3) | ⬜ | — | — |
| P6-04 | Escalation cap + `LevelAdvance` node | ⬜ | — | — |

## Phase 7: Stitch UI + Onboarding (Week 7)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P7-01 | Stitch MCP design system (Apple-dark, Geist) | ⬜ | — | — |
| P7-02 | `ChallengePanel` component | ⬜ | — | — |
| P7-03 | `CodeReviewStream` component (SSE + virtualized) | ⬜ | — | — |
| P7-04 | `SkillsRadarMap` + `SkillBarMeter` components | ⬜ | — | — |
| P7-05 | `LevelBadge` + `EscalationGauge` components | ⬜ | — | — |
| P7-06 | `SubmissionHistory` (virtualized list) | ⬜ | — | — |
| P7-07 | `OnboardingWizard` (6-step calibration) | ⬜ | — | — |
| P7-08 | Assessment workspace page route | ⬜ | — | — |

## Phase 8: Enterprise (Week 8)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P8-01 | NextAuth.js (credentials + GitHub + Google) | ⬜ | — | — |
| P8-02 | RBAC middleware (candidate / reviewer / admin) | ⬜ | — | — |
| P8-03 | Organization + Cohort CRUD | ⬜ | — | — |
| P8-04 | Org dashboard (heatmap, export, audit) | ⬜ | — | — |
| P8-05 | W3C VC credential issuer + verifier | ⬜ | — | — |
| P8-06 | GitHub CI/CD integration (App + webhook) | ⬜ | — | — |

## Phase 9: Observability + Launch (Week 9)

| # | Ticket | Status | Assignee | Started |
|---|--------|--------|----------|---------|
| P9-01 | Prometheus + Grafana dashboards | ⬜ | — | — |
| P9-02 | OpenTelemetry distributed tracing | ⬜ | — | — |
| P9-03 | k6 Load test scripts (1000 concurrent) | ⬜ | — | — |
| P9-04 | Docker Compose assessment services | ⬜ | — | — |
| P9-05 | Railway deploy config | ⬜ | — | — |
| P9-06 | Security audit + dependency scan | ⬜ | — | — |
| P9-07 | Documentation (API + deploy + user guide) | ⬜ | — | — |

---

## Quick Stats

| Phase | Tickets | Done | Progress |
|-------|---------|------|----------|
| P1: Foundation | 6 | 0 | 0% |
| P2: LangGraph | 8 | 0 | 0% |
| P3: RAG | 6 | 0 | 0% |
| P4: Sandbox | 5 | 0 | 0% |
| P5: BullMQ+SSE | 5 | 0 | 0% |
| P6: Go Harder | 4 | 0 | 0% |
| P7: Stitch UI | 8 | 0 | 0% |
| P8: Enterprise | 6 | 0 | 0% |
| P9: Launch | 7 | 0 | 0% |
| **Total** | **55** | **0** | **0%** |