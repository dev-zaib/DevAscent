# DevAscent — Ticket Tracking Board

> **Repo:** `git@github.com-dev-zaib:dev-zaib/DevAscent.git`
> **Base:** Forked from `NousResearch/hermes-agent` (MIT, v0.17.0)
> **Last updated:** 2026-06-23
> **Commit:** `c467f09` (9 commits since fork)

| Status Key |
|-----------|
| ⬜ `todo` · 🟦 `in_progress` · ✅ `done` · ❌ `skipped` |

---

## Phase 1: Fork & Foundation ✅

| # | Ticket | Status |
|---|--------|--------|
| P1-01 | Strip unused gateway platforms + tools | ✅ |
| P1-02 | Rename `hermes` → `devascent` across codebase | ✅ |
| P1-03 | Add PostgreSQL + Redis + assessment deps | ✅ |
| P1-04 | Create `devascent/` Python package | ✅ |
| P1-05 | Define PostgreSQL data models + Alembic | ✅ |
| P1-06 | Assessment API spec + FastAPI app | ✅ |

## Phase 2: LangGraph State Machine ✅

| # | Ticket | Status |
|---|--------|--------|
| P2-01 | `DevAscentState` typed dict + Pydantic validation | ✅ |
| P2-02 | LangGraph state graph with PG checkpointer | ✅ |
| P2-03 | `InitializeAssessment` node | ✅ |
| P2-04 | `PresentChallenge` node | ✅ |
| P2-05 | `EvaluateSubmission` node + rubric engine | ✅ |
| P2-06 | `UpdateSkillsMatrix` node | ✅ |
| P2-07 | `DetermineNextStep` router + conditional edges | ✅ |
| P2-08 | Assessment API endpoints wired to graph | ✅ |

## Phase 3: RAG Pipeline ✅

| # | Ticket | Status |
|---|--------|--------|
| P3-01 | pgvector extension + challenge table | ✅ |
| P3-02 | Embedding generation service | ✅ |
| P3-03 | Seed 16 enterprise challenges | ✅ |
| P3-04 | `ChallengeRetriever` similarity search | ✅ |
| P3-05 | User weak spot embedding generator | ✅ |
| P3-06 | Integrate retriever into `PresentChallenge` | ✅ |

## Phase 4: Sandbox Executor ✅

| # | Ticket | Status |
|---|--------|--------|
| P4-01 | gVisor sandbox Docker runtime support | ✅ |
| P4-02 | `SandboxExecutor` (Docker + subprocess fallback) | ✅ |
| P4-03 | Seccomp profile + resource limits | ✅ |
| P4-04 | Constraint validator (post-escalation checks) | ✅ |
| P4-05 | Rate limiter (Redis sliding window) | ✅ |

## Phase 5: BullMQ + SSE ✅

| # | Ticket | Status |
|---|--------|--------|
| P5-01 | BullMQ + ioredis in web package | ✅ |
| P5-02 | Evaluation worker (TS → Python subprocess) | ✅ |
| P5-03 | SSE endpoint + `sse-starlette` | ✅ |
| P5-04 | SSE client hook (`useSSE`) | ✅ |
| P5-05 | `POST /submit` → 202 + stream URL | ✅ |

## Phase 6: Go Harder Escalation ✅

| # | Ticket | Status |
|---|--------|--------|
| P6-01 | `EscalateChallenge` LangGraph node | ✅ |
| P6-02 | Escalation prompt template (depth-aware) | ✅ |
| P6-03 | Constraint catalog (depth 1-3) | ✅ |
| P6-04 | Escalation cap + `LevelAdvance` node | ✅ |

## Phase 7: Stitch UI + Workspace

| # | Ticket | Status |
|---|--------|--------|
| P7-01 | Stitch MCP design system (Apple-dark, Geist) | ❌ (built directly with Tailwind instead) |
| P7-02 | `ChallengePanel` component | ✅ |
| P7-03 | `CodeReviewStream` component (SSE + virtualized) | ✅ |
| P7-04 | `SkillsRadarMap` + `SkillBarMeter` components | ✅ |
| P7-05 | `LevelBadge` + `EscalationGauge` components | ✅ |
| P7-06 | `SubmissionHistory` (virtualized list) | ✅ |
| P7-07 | `OnboardingWizard` (6-step calibration) | ❌ (not needed for personal use) |
| P7-08 | Assessment workspace page route | ✅ |

## Phase 8: Enterprise

| # | Ticket | Status |
|---|--------|--------|
| P8-01 | NextAuth.js (credentials + GitHub + Google) | ❌ |
| P8-02 | RBAC middleware (candidate / reviewer / admin) | ❌ |
| P8-03 | Organization + Cohort CRUD | ❌ |
| P8-04 | Org dashboard (heatmap, export, audit) | ❌ |
| P8-05 | W3C VC credential issuer + verifier | ❌ |
| P8-06 | GitHub CI/CD integration (App + webhook) | ❌ |

## Phase 9: Observability + Launch

| # | Ticket | Status |
|---|--------|--------|
| P9-01 | Prometheus + Grafana dashboards | ❌ |
| P9-02 | OpenTelemetry distributed tracing | ❌ |
| P9-03 | k6 Load test scripts | ❌ |
| P9-04 | Docker Compose assessment services | ❌ |
| P9-05 | Railway deploy config | ❌ |
| P9-06 | Security audit + dependency scan | ❌ |
| P9-07 | Documentation (API + deploy + user guide) | ❌ |

---

## Quick Stats

| Phase | Tickets | Done | Skipped | Progress |
|-------|---------|------|---------|----------|
| P1: Foundation | 6 | 6 | 0 | 100% |
| P2: LangGraph | 8 | 8 | 0 | 100% |
| P3: RAG | 6 | 6 | 0 | 100% |
| P4: Sandbox | 5 | 5 | 0 | 100% |
| P5: BullMQ+SSE | 5 | 5 | 0 | 100% |
| P6: Go Harder | 4 | 4 | 0 | 100% |
| P7: Stitch UI | 8 | 6 | 2 | 75% |
| P8: Enterprise | 6 | 0 | 6 | Skipped |
| P9: Launch | 7 | 0 | 7 | Skipped |
| **Total** | **55** | **40** | **15** | **73%** |

---

## What's Built

```
devascent/                         ← Assessment engine (43 Python files)
├── assessment/
│   ├── state.py                   ← DevAscentState TypedDict + Pydantic
│   ├── state_graph.py             ← LangGraph graph + PostgresSaver
│   ├── router.py                  ← Score-based conditional routing
│   ├── nodes/
│   │   ├── initialize.py          ← Boot assessment session
│   │   ├── present.py             ← RAG-driven challenge selection
│   │   ├── evaluate.py            ← Sandbox exec → rubric scoring
│   │   ├── update_skills.py       ← Decay-weighted recalculation
│   │   ├── determine_next.py      ← Advance / escalate / reinforce
│   │   └── escalate.py            ← Go Harder constraint injection
│   └── evaluator/
│       ├── rubric.py              ← Weighted scoring rubric engine
│       ├── sandbox.py             ← gVisor Docker + subprocess executor
│       ├── seccomp.json           ← 300+ syscall allowlist
│       └── constraint_validator.py ← Post-escalation pattern checks
├── rag/
│   ├── embedder.py                ← OpenAI text-embedding-3-small
│   ├── retriever.py               ← pgvector similarity search + dedup
│   └── seed_data.py               ← 16 enterprise challenges
├── api/
│   ├── app.py                     ← FastAPI with CORS
│   ├── routes/assessment.py       ← /start, /submit, /state, /next
│   ├── routes/stream.py           ← SSE /stream/:jobId
│   └── middleware/rate_limit.py   ← Redis sliding window 10/hr
├── db/
│   ├── base.py                    ← SQLAlchemy async engine
│   ├── models/                    ← User, Challenge, Assessment, Org, Cohort
│   └── migrations/                ← Alembic async + init migration
├── config.py
└── cert/ analytics/ queue/        ← Placeholder for future phases

web/src/                           ← Assessment UI (8 React components)
├── components/assessment/
│   ├── ChallengePanel.tsx         ← Markdown renderer + rubric + hints
│   ├── CodeReviewStream.tsx       ← Real-time SSE evaluation display
│   ├── SkillsRadarMap.tsx         ← SVG radar chart + SkillBarMeter
│   ├── LevelBadge.tsx             ← Animated level indicator
│   ├── EscalationGauge.tsx        ← 4-step escalation intensity
│   └── SubmissionHistory.tsx      ← Virtualized attempt log
├── hooks/
│   ├── useSSE.ts                  ← EventSource with reconnect
│   └── useAssessment.ts           ← Session state + submission
├── pages/assess/[sessionId].tsx   ← 3-panel split workspace
└── lib/queue.ts                   ← BullMQ producer

web/worker/
└── evaluation.worker.ts           ← TS worker → Python LangGraph subprocess
```

## Commits

```
c467f09 P5+7: BullMQ worker, SSE hooks, and assessment UI components
4766bd1 P4: sandbox executor, constraint validator, rate limiter
51e8f5d P3: RAG pipeline with 16 enterprise challenges
fd06276 P2: LangGraph assessment state machine
c49d1ec P1-06: FastAPI assessment API with SSE streaming
29ae5f9 P1-05: Alembic async migration setup with initial schema
07d726f P1-03+04: add assessment deps and devascent/ Python package
f7a87ea P1-02: rename hermes → devascent across codebase
86b63f5 P1-01: strip unused platforms, desktop, TUI, optional skills
211ba9c feat(agent): one-shot LLM helper (upstream Hermes)
```

---

## Phase 10: Skill Coach — un-silo the assessment engine (NEW)

> **Why:** the assessment FSM wrote only to its own LangGraph/Postgres
> checkpoint and never fed back into a skill-building loop. Hermes ships
> cross-session memory + a self-improving skills system — none of it was
> wired to the assessment. This phase closes that gap: every evaluation now
> compounds into a durable, growing personal curriculum.

| Ticket | Description | Status |
|--------|-------------|--------|
| P10-01 | `LearningJournal` — durable per-user JSONL of every evaluation | ✅ |
| P10-02 | Curriculum + spaced-repetition engine (SM-2 inspired, pure) | ✅ |
| P10-03 | `CoachReport` synthesis (mastery, momentum, strongest/weakest) | ✅ |
| P10-04 | Memory bridge — writes hermes-format progress note for the agent | ✅ |
| P10-05 | `CoachProgress` LangGraph node wired after `update_skills` | ✅ |
| P10-06 | Coach API: `/api/coach/progress|curriculum|history/{user_id}` | ✅ |
| P10-07 | Cron-ready daily practice reminder (`python -m devascent.coach.reminder`) | ✅ |
| P10-08 | Unit tests (11, infra-free — no DB/Redis/langgraph) | ✅ |

**Brought back from the strip (P1-01):**
- The **self-improving skills + memory loop** is reconnected via the memory
  bridge — the agent can now coach with full skill-history awareness.
- The **cron** subsystem (kept, but unused) now has a real job: daily
  spaced-repetition practice nudges toward the user's weakest skills.

**Run the new tests:**
```
PYTHONPATH=. .venv/bin/python tests/devascent/test_coach.py
```

---

## Phase 11: DeepSeek + UI redesign (NEW)

| Ticket | Description | Status |
|--------|-------------|--------|
| P11-01 | DeepSeek evaluator (`devascent/llm/deepseek.py`, stdlib, OpenAI-compatible) | ✅ |
| P11-02 | Wire DeepSeek + coach journal into the demo API submit path | ✅ |
| P11-03 | First-observation seeding fix (no decay-vs-zero understatement) | ✅ |
| P11-04 | Full UI redesign — gamified, clutter-free single-page app (`web/public/assess.html`) | ✅ |
| P11-05 | Run + verify end-to-end (uvicorn, real DeepSeek grading) | ✅ |

**UI:** Apple-dark premium aesthetic, onboarding hero, XP/level/streak, animated
mastery ring + skill radar, live coach panel, spaced-repetition "practice next",
score-reveal with Go-Harder escalation. Vanilla JS, zero build, served by FastAPI.

**Run:**
```
DEEPSEEK_API_KEY=... PYTHONPATH=. .venv/bin/python -m uvicorn devascent.api.app:app --port 8000
# open http://127.0.0.1:8000
```

---

## Phase 13: Pivot — "Path to Top 1%" interactive learning studio (NEW)

> Rethink: the assessment-only app felt like being *tested*. Pivoted to a
> career-ladder engine: current role → AI roadmap → narrated/animated/playable
> lessons → interview/test to prove mastery. Apple-level, Claude warm-light theme.

| Ticket | Description | Status |
|--------|-------------|--------|
| P13-01 | DeepSeek generators: roadmap, lesson (narration+mermaid+playable widget), interview Qs, answer grading | ✅ |
| P13-02 | Routes: `/api/roadmap`, `/api/learn/lesson`, `/api/interview/{start,grade}`, `/api/tts` (+offline mocks) | ✅ |
| P13-03 | React SPA (separate Vite entry `devascent.html`): Onboard → Roadmap (React Flow graph) | ✅ |
| P13-04 | Studio (Learn): narrated lesson (Web Speech + sentence highlight), Mermaid concept map, sandboxed playable widget | ✅ |
| P13-05 | Prove (Interview): question flow + DeepSeek grading → journal/coach update → roadmap re-orders | ✅ |
| P13-06 | Local TTS: Kokoro-82M endpoint + `scripts/setup_tts.sh` + browser fallback | ✅ |
| P13-07 | Warm Apple-light design system (Claude-style, clay accent), motion, persistence | ✅ |

**Researched (LLM interactive-learning prior art):** LangChain LLM Graph Transformer,
ai-knowledge-graph, AnimatedLLM, Interactive Sketchpad/SPROUT, Manim generators
(manim-generator, Math-To-Manim). Chose client-side interactive (graphs/Mermaid/iframe
widgets) over Manim video render for instant interactivity. TTS: Kokoro-82M (CPU, 327MB)
local, Web Speech default.

**Run:** `PYTHONPATH=. .venv/bin/python -m uvicorn devascent.api.app:app --port 8000` → http://127.0.0.1:8000
**Rebuild UI after edits:** `cd web && npx vite build`
**Premium voice (optional):** `scripts/setup_tts.sh`
