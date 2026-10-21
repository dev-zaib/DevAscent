# DevAscent — Complete Feature Story Breakdown

> **Strategy:** Fork [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) (MIT, 200k ★, Python 82.6% / TypeScript 13.4%) and mutate it into DevAscent. Hermes already ships: agent loop, skills system, memory, MCP gateway, Docker, cron, multi-platform gateway, TUI, and a learning loop (skills auto-create and self-improve). We bolt on the assessment engine, RAG pipeline, LangGraph state machine, BullMQ queues, and the Stitch MCP assessment UI. This cuts ~60% of the build effort.

---

## Feature 1: LangGraph Assessment State Machine

### Story
**As a** platform engineer,  
**I want** an intelligent state machine that manages every candidate's assessment journey,  
**So that** no context is lost, skill progression is deterministic and auditable, and the system never skips foundational concepts.

### Hermes Fork Integration
Hermes ships `hermes_state.py` — a session/state manager. We extend this into a full LangGraph-backed state graph. Hermes already tracks conversation state, user profiles (`Honcho` dialectic modeling), and memory. We add assessment-specific state dimensions.

### Acceptance Criteria

**State Schema (`DevAscentState`)**
```typescript
interface DevAscentState {
  userId: string;
  currentLevel: 'BASELINE' | 'SYSTEM_DESIGNER' | 'TOP_1_PERCENT' | 'ARCHITECT' | 'DISTINGUISHED';
  skillsMatrix: Record<string, number>; // 0-100 per skill dimension
  activeChallengeId: string;
  challengeAttempt: number;             // retry counter
  evaluationHistory: EvaluationLog[];
  escalationDepth: number;              // how many times "Go Harder" triggered
  sessionStartTime: string;
  lastEvaluationTimestamp: string;
}

interface EvaluationLog {
  challengeId: string;
  score: number;
  rubricBreakdown: Record<string, number>;
  aiFeedback: string;
  constraintsApplied: string[];
  timestamp: string;
}
```

**LangGraph Nodes (minimum 5)**

| Node | Responsibility |
|------|---------------|
| `InitializeAssessment` | Boots state from PostgreSQL, seeds vector-retrieved challenge |
| `PresentChallenge` | Renders challenge markdown + workspace context to the user |
| `EvaluateSubmission` | Runs submitted code against rubric via sandboxed executor |
| `UpdateSkillsMatrix` | Weighted recalculation using performance + decay factor |
| `DetermineNextStep` | Conditional router: advance / keep-with-variant / demote / escalate |

**Routing Logic**
```
Score >= 85% on BASELINE  → route to EscalateChallenge (Go Harder)
Score >= 85% on escalated → advance level, expand skills matrix
Score >= 70%               → keep level, serve variant challenge
Score < 70%                 → demote or reinforce weak dimensions
Score < 40%                 → flag for human review, pause assessment
```

**Hermes Mutation Required**
- Fork `hermes_state.py` → `dev_ascent_state.py` with LangGraph nodes
- Add `StateGraph` from `@langchain/langgraph` (TypeScript bindings) alongside Hermes's Python core
- Wire LangGraph checkpointer to PostgreSQL (Hermes already has a DB layer — extend it)
- Expose graph state via a REST endpoint the Stitch UI polls

### Subtasks
1. Install LangGraph (TypeScript) + `@langchain/langgraph-checkpoint-postgres`
2. Define `DevAscentState` interface and Zod validation schema
3. Implement 5 LangGraph nodes with typed inputs/outputs
4. Add conditional edge logic in `DetermineNextStep`
5. Wire PostgreSQL checkpointer for state persistence across sessions
6. Build REST endpoints: `POST /assessment/start`, `POST /assessment/submit`, `GET /assessment/state/:userId`
7. Unit tests for each node's state transitions
8. Integration test: full flow BASELINE → SYSTEM_DESIGNER

---

## Feature 2: Vector-Driven RAG Assessment Pipeline

### Story
**As a** candidate aiming for elite engineering roles,  
**I want** the platform to pull real-world, production-grade scenarios from a curated enterprise challenge repository,  
**So that** I'm tested on practical problems (memory leaks, connection pooling, rate-limiting) instead of toy algorithms.

### Hermes Fork Integration
Hermes already has: FTS5 session search, LLM summarization for recall, and tool-based RAG patterns. We add pgvector as a first-class embedding store. Hermes's existing memory system (`MEMORY.md`, skills) becomes the user profile for retrieval — we vectorize the user's weak spots and query challenges that target them.

### Acceptance Criteria

**Database Layer**
- `challenges` table with `embedding vector(1536)` column (pgvector)
- `user_weak_spots` table with `embedding vector(1536)` — regenerated after each `UpdateSkillsMatrix` run
- Index: IVFFlat or HNSW on both embedding columns

**Embedding Pipeline**
- Use `text-embedding-3-small` (OpenAI) or Nous's own embeddings via Portal
- Chunking: challenges split into (title, description, rubric, constraints, solution_hints)
- User weak spot embedding: concatenate lowest-3 skill names + descriptions

**Retrieval Strategy**
- When `generateChallenge` node fires, execute:

```sql
SELECT challenge_id, title, 1 - (embedding <=> $user_weak_embedding) AS similarity
FROM challenges
WHERE target_skills && $weak_skill_names
ORDER BY embedding <=> $user_weak_embedding
LIMIT 5;
```

- From top-5, select the one with the lowest prior attempt count for this user (avoid repeats)
- Fallback: random weighted selection from un-attempted challenges

**Seed Data (15+ Scenarios)**
| # | Scenario | Target Skill |
|---|----------|-------------|
| 1 | Redis-backed async task queues under viral traffic | async_flows, caching |
| 2 | Database connection pool exhaustion debug | connection_pooling, postgres |
| 3 | Memory leak in long-running Node.js worker | memory_management, profiling |
| 4 | Rate-limiting distributed API gateway | rate_limiting, redis |
| 5 | Row virtualization for 50k-record data grid | rendering, performance |
| 6 | Web scraper with headless browser pool | scraping, concurrency |
| 7 | Event-driven microservice with dead-letter queue | messaging, fault_tolerance |
| 8 | Idempotent payment processing with idempotency keys | idempotency, transactions |
| 9 | Circuit breaker for flaky external dependency | resilience, patterns |
| 10 | API pagination with cursor-based pagination | api_design, postgres |
| 11 | JWT rotation with refresh token blacklisting | auth, security |
| 12 | Distributed lock with Redlock algorithm | distributed_systems, redis |
| 13 | WebSocket fan-out with backpressure | realtime, backpressure |
| 14 | Multi-tenant Postgres RLS policy design | multi_tenancy, security |
| 15 | Semantic caching layer for LLM responses | caching, embeddings |
| 16 | Graceful shutdown for Dockerized Node.js service | deployment, signal_handling |

### Subtasks
1. Enable pgvector extension in PostgreSQL
2. Create `challenges` and `user_weak_spots` tables with vector columns
3. Write embedding generation service (OpenAI or Nous Portal provider)
4. Implement seed data migration script with automatic embedding
5. Build `ChallengeRetriever` class with similarity search + dedup logic
6. Integrate retriever into LangGraph `PresentChallenge` node
7. Regenerate user weak-spot embeddings on every `UpdateSkillsMatrix` run
8. Write retrieval accuracy tests (manual: verify challenges match weak skills)

---

## Feature 3: The "Go Harder" Adaptive Escalation Engine

### Story
**As an** engineer who just crushed a baseline task,  
**I want** the system to immediately inject brutal, unexpected production constraints into my workspace,  
**So that** I'm forced to refactor under pressure — exactly like a real production incident.

### Hermes Fork Integration
Hermes already has a "self-improvement loop" where skills auto-create and improve after complex tasks. We extend this pattern: after a high-score evaluation, instead of completing, the agent injects a mutation prompt. Hermes's existing tool-calling system and code execution sandbox become the environment where the escalated challenge plays out.

### Acceptance Criteria

**Trigger Mechanism**
```
IF EvaluateSubmission.score >= 85% AND currentLevel === 'BASELINE'
  AND escalationDepth < 3  // cap at 3 escalations per level
THEN
  route to EscalateChallenge node
ELSE IF EvaluateSubmission.score >= 85% AND currentLevel !== 'BASELINE'
  route to LevelAdvance node
```

**Mutation Prompting Architecture**

The `EscalateChallenge` node calls an LLM with a structured prompt template:

```
You are modifying a completed engineering challenge to add chaos.

ORIGINAL CHALLENGE: {original_challenge_markdown}
USER'S SOLUTION SUMMARY: {solution_summary}
CURRENT SKILLS MATRIX: {skills_matrix}
ESCALATION DEPTH: {escalation_depth}

ADD THESE CONSTRAINT TYPES (pick 2-3 based on depth):
Level 1 (depth=1): Scale constraint, latency constraint, data volume spike
Level 2 (depth=2): Fault injection, network partition, resource exhaustion
Level 3 (depth=3): Security incident, multi-region failover, schema migration mid-incident

OUTPUT: Modified challenge markdown with new constraints appended.
DO NOT remove the original requirements. ADD to them.
```

**Example Escalation Chain**
```
Challenge 1: "Build a TypeScript web scraper"
  → Pass at 92%

Escalation 1 (depth=1):
  "A viral traffic spike hits. Rewrite this scraper using Redis-backed 
   async task queues, add semantic caching to avoid re-fetching identical 
   data within 60s windows, AND implement row virtualization to render 
   50,000 scraped records without UI lag."
  → Pass at 88%

Escalation 2 (depth=2):
  "Your Redis cluster just lost quorum. Implement a fallback mechanism 
   using in-memory LRU cache with TTL. Add circuit breaker around the 
   scraper's HTTP client so one failing target doesn't block the queue. 
   Log every failure to a dead-letter topic for later replay."
  → Needs work at 67% (re-routes to reinforcement)
```

**Validation Hooks**
- `EvaluateSubmission` must check for new constraints explicitly:
  - If escalation added "Redis queue" → verify Redis usage in solution
  - If escalation added "circuit breaker" → verify pattern implementation
  - If escalation added "row virtualization" → verify render strategy
- Constraints not implemented → automatic 15-point penalty per missing constraint

### Subtasks
1. Build `EscalateChallenge` LangGraph node
2. Create escalation prompt template with depth-aware constraint selection
3. Implement constraint validation hooks in `EvaluateSubmission`
4. Add `escalationDepth` tracking to state
5. Build `LevelAdvance` node for post-escalation promotion
6. Implement escalation cap (max 3 per level)
7. Write unit tests for escalation triggering logic
8. Integration test: full BASELINE → 3 escalations → level advance

---

## Feature 4: Apple-Minimalist Assessment Workspace (Stitch MCP + Geist)

### Story
**As a** developer who values clean tooling,  
**I want** a distraction-free split workspace with the challenge, my code, and live metrics side-by-side,  
**So that** I can focus entirely on the engineering problem without visual noise.

### Hermes Fork Integration
Hermes already has a web UI (`web/` directory, TypeScript), a TUI (`ui-tui/`), and MCP integration. We generate the assessment workspace using Google Stitch MCP as an additional frontend surface. Hermes's gateway routes traffic to both the Stitch UI and the existing Hermes interfaces.

### Acceptance Criteria

**Design Tokens (Apple-style)**
- **Fonts:** Geist Sans (headlines), Inter (body), JetBrains Mono (code)
- **Mode:** True dark mode — `#0a0a0a` backgrounds, `#fafafa` text
- **Accent:** Single ghost-white stroke, no gradients
- **Roundness:** `ROUND_EIGHT` (subtle, not pill-shaped)
- **Spacing:** Large padding system — `16px` / `24px` / `32px` / `48px`

**Three-Panel Split Layout**

```
┌──────────────────┬──────────────────────────┬──────────────────┐
│  LEFT PANEL      │  CENTER PANEL            │  RIGHT PANEL     │
│  (360px)         │  (flex-1)                │  (400px)         │
├──────────────────┼──────────────────────────┼──────────────────┤
│ Challenge        │ Code Review /            │ Live Metrics     │
│ Markdown         │ Submission Log           │ Dashboard        │
│                  │                          │                  │
│ • Requirements   │ • Submitted code         │ • Radar chart    │
│ • Architecture   │   (syntax highlighted)   │ • Skill bars     │
│ • Constraints    │ • AI evaluation stream   │ • Level badge    │
│ • Hints (toggle) │ • Rubric breakdown       │ • Attempt history│
│                  │ • Timestamps             │ • Escalation     │
│                  │                          │   depth gauge    │
│                  │ Terminal output stream   │                  │
│                  │ (virtualized)            │                  │
└──────────────────┴──────────────────────────┴──────────────────┘
```

**Component Specs**
1. **ChallengePanel** — Markdown renderer with collapsible sections, copy-to-clipboard, fullscreen toggle
2. **CodeReviewStream** — SSE-connected terminal that streams AI evaluation results character-by-character with syntax highlighting
3. **SkillsRadarMap** — SVG-based radar chart with 6-8 skill axes, animated transitions on score update
4. **SkillBarMeter** — Horizontal bar stack showing each skill's score (0-100), color-coded green→yellow→red
5. **LevelBadge** — Animated level indicator (BASELINE → SYSTEM_DESIGNER → TOP_1_PERCENT)
6. **EscalationGauge** — Shows escalation depth (0-3) with increasing intensity
7. **SubmissionHistory** — Virtualized list of past attempts with score and timestamp

**Performance**
- Window virtualization (`@tanstack/react-virtual`) for terminal logs and submission history
- `react-markdown` with lazy-load for challenge content
- SSE stream with buffer management (max 500 lines in DOM at once)

### Subtasks
1. Generate base UI screens via Google Stitch MCP with the Apple design system
2. Implement ChallengePanel with markdown rendering
3. Build CodeReviewStream with SSE connection and virtualization
4. Create SkillsRadarMap SVG component
5. Create SkillBarMeter component
6. Build LevelBadge and EscalationGauge
7. Implement SubmissionHistory with virtualized list
8. Add responsive breakpoints (3-panel → stacked on tablet)
9. Wire all components to assessment state API

---

## Feature 5: Asynchronous Evaluation Pipeline (BullMQ + SSE)

### Story
**As a** platform operator,  
**I want** code evaluations to run asynchronously through a job queue backed by Redis,  
**So that** the web server never times out, the frontend stays responsive, and heavy AI evaluations don't block other users.

### Hermes Fork Integration
Hermes already has Redis integration (for sessions, caching, pub/sub) and Docker deployment with Redis. We add BullMQ workers. Hermes's agent loop becomes the worker's execution context — when a job is picked up, it runs through the LangGraph evaluation, calls the LLM provider (Hermes already supports Nous Portal, OpenRouter, OpenAI, etc.), and streams results back via SSE.

### Acceptance Criteria

**Queue Architecture**
```
POST /api/assessment/submit
     │
     ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Web Server │────▶│  Redis      │────▶│  BullMQ Worker   │
│  (Express)  │     │  (BullMQ)   │     │  (Railway)       │
│             │◀────│             │◀────│                  │
│  202 Accept │     │  Job Queue  │     │  LangGraph.run() │
│  SSE stream │     │  Pub/Sub    │     │  LLM evaluate    │
└─────────────┘     └─────────────┘     │  Save to PG      │
                                        └──────────────────┘
```

**API Surface**
| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/api/assessment/submit` | POST | Enqueue evaluation job | `202 { jobId, streamUrl }` |
| `/api/assessment/stream/:jobId` | GET | SSE stream of evaluation | `text/event-stream` |
| `/api/assessment/result/:jobId` | GET | Poll for final result | `200 { score, feedback, skillsMatrix }` |
| `/api/assessment/state/:userId` | GET | Current assessment state | `200 DevAscentState` |

**SSE Event Types**
```
event: progress
data: {"stage": "evaluating", "message": "Analyzing async flow implementation..."}

event: rubric
data: {"dimension": "async_flows", "score": 85, "feedback": "..."}

event: skills_update
data: {"skillsMatrix": {"async_flows": 85, "connection_pooling": 72}}

event: complete
data: {"finalScore": 85, "nextAction": "escalate", "challengeId": "..."}

event: error
data: {"code": "TIMEOUT", "message": "Evaluation exceeded 120s limit"}
```

**BullMQ Configuration**
- Queue: `dev-ascent-evaluations`
- Concurrency: 5 jobs per worker
- Timeout: 120s per job
- Retry: 3 attempts with exponential backoff (5s, 25s, 125s)
- Dead letter: failed jobs → `dev-ascent-dlq` for manual review
- Redis connection: pool of 10, keepalive

**Railway Deployment**
```yaml
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile.worker"

[deploy]
numReplicas = 3
healthcheckPath = "/health"
restartPolicyMaxRetries = 10

[service]
port = 3001
```

### Subtasks
1. Install BullMQ + ioredis in the backend package
2. Create `evaluation-queue.ts` with job type definitions
3. Build webhook handler: `POST /api/assessment/submit` → enqueue job → 202
4. Build SSE endpoint: `GET /api/assessment/stream/:jobId` with event sourcing
5. Create BullMQ worker that invokes LangGraph state machine
6. Wire LLM provider call inside worker (reuse Hermes provider layer)
7. Implement job timeout, retry, and dead-letter logic
8. Create Dockerfile.worker for Railway deployment
9. Add health check endpoint for worker
10. Write integration test: submit → stream → verify result

---

---

# ADDITIONAL FEATURES (Beyond Prompt)

These are production-necessary features not in the original spec.

---

## Feature 6: Secure Code Execution Sandbox

### Story
**As a** platform security engineer,  
**I want** all user-submitted code to execute in an isolated, resource-constrained sandbox,  
**So that** malicious code cannot escape, no container breakout is possible, and no single user can consume all cluster resources.

### Acceptance Criteria

**Sandbox Architecture**
- gVisor (runsc) runtime for Docker — kernel-level syscall filtering
- Docker container per submission with tight limits:
  - CPU: 1 vCPU
  - Memory: 512MB
  - Disk: 1GB tmpfs (ephemeral, wiped after run)
  - Network: none (no outbound access)
  - Timeout: 30s wall clock
- stdin/stdout only — no file system writes persist
- Container lifecycle: create → copy code → execute → capture output → destroy (all under 5s)

**Supported Languages & Runtimes**
| Language | Runtime | Version |
|----------|---------|---------|
| TypeScript | `ts-node` / `bun` | 5.x / 1.x |
| Python | CPython | 3.11 |
| Go | Go | 1.22 |
| Rust | cargo-script | stable |

**Security Hardening**
- `seccomp` profile: allow only `read`, `write`, `exit`, `sigreturn`, `mmap`, `brk`
- No `/proc` access
- No `/sys` access
- `NO_NEW_PRIVILEGES` flag
- `read-only` root filesystem
- Rate limit: 10 submissions per user per hour

### Subtasks
1. Build Docker sandbox image with gVisor runtime
2. Implement `SandboxExecutor` class with create/run/destroy lifecycle
3. Add language detection and runtime selection
4. Apply seccomp, cgroup, and capability drop constraints
5. Build submission rate limiter (Redis-based sliding window)
6. Write sanitization tests: fork bomb, disk fill, network access, /proc read

---

## Feature 7: Multi-Tenant Auth & Organization Management

### Story
**As a** company CTO,  
**I want** to onboard my entire engineering team, assign them to cohorts, and track their assessment progress in aggregate,  
**So that** I can identify skill gaps across my org and make data-driven hiring/promotion decisions.

### Acceptance Criteria

**Auth System**
- NextAuth.js v5 with:
  - Email/password (credentials provider)
  - GitHub OAuth
  - Google OAuth
  - SSO/SAML (for enterprise)
- JWT-based sessions with refresh token rotation
- Role-based access: `candidate`, `reviewer`, `org_admin`, `platform_admin`

**Organization Model**
```typescript
interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: 'free' | 'pro' | 'enterprise';
  members: OrgMember[];
  cohorts: Cohort[];
  settings: OrgSettings;
}

interface Cohort {
  id: string;
  name: string;
  memberIds: string[];
  assessmentBatch: string; // links to a set of challenges
  startDate: string;
  endDate: string;
}

interface OrgSettings {
  allowedDomains: string[];
  requireSso: boolean;
  maxConcurrentAssessments: number;
}
```

**Org Dashboard**
- Aggregate skills matrix heatmap across cohort
- Individual candidate progress tracker
- Cohort comparison (A vs B) with statistical significance
- Export: CSV, PDF report
- Audit log: who viewed what, when

### Subtasks
1. Install and configure NextAuth.js v5
2. Implement credentials + OAuth providers
3. Create RBAC middleware for API routes
4. Build organization CRUD API + UI
5. Build cohort management UI (drag-drop members, set batch)
6. Create aggregate analytics dashboard
7. Implement audit logging
8. Build CSV/PDF export endpoints

---

## Feature 8: LLM Provider Abstraction Layer

### Story
**As a** platform architect,  
**I want** a pluggable LLM provider system that supports multiple backends without code changes,  
**So that** I can switch between OpenAI, Anthropic, open-source models, and Nous Portal based on cost, latency, and capability needs.

### Hermes Fork Integration
Hermes already has an excellent provider system (`providers/` directory) supporting Nous Portal, OpenRouter, OpenAI, Anthropic, Hugging Face, and more. We extend this to add evaluation-specific provider routing (fast model for simple rubric checks, powerful model for architectural feedback).

### Acceptance Criteria

**Provider Router**
```typescript
interface ProviderConfig {
  defaultProvider: 'openai' | 'anthropic' | 'nous-portal' | 'openrouter' | 'custom';
  routing: {
    evaluation: 'anthropic';      // Claude for deep code review
    challenge_generation: 'openai'; // GPT-4o for challenge creation
    escalation_prompting: 'anthropic'; // Claude for creative chaos
    embedding: 'openai';           // text-embedding-3-small
  };
  fallback: {
    provider: 'openrouter';
    models: string[];
  };
}
```

**Model Registry**
| Task | Primary Model | Reasoning |
|------|--------------|-----------|
| Code evaluation | Claude Sonnet 4 | Best code review capabilities |
| Challenge generation | GPT-4o | Cost-effective for batch gen |
| Escalation mutation | Claude Opus 4 | Most creative constraint injection |
| Embeddings | text-embedding-3-small | 1536d, fast, cheap |
| Sandbox feedback | GPT-4o-mini | Fast, sufficient for syntax checks |

**Provider Health Checks**
- Latency SLA: <5s p95 per call
- Circuit breaker: 5 consecutive failures → route to fallback
- Cost tracking: per-user, per-organization token/credit accounting

### Subtasks
1. Fork Hermes `providers/` directory
2. Add provider router with per-task model selection
3. Implement circuit breaker pattern for fallback routing
4. Build cost tracking middleware
5. Create provider health dashboard
6. Write provider-agnostic test harness

---

## Feature 9: Real-Time Collaboration (Multiplayer Assessment)

### Story
**As a** reviewer,  
**I want** to watch a candidate's code submission stream in real-time and provide live annotations,  
**So that** I can give immediate feedback during pair-programming-style assessments.

### Acceptance Criteria

**WebSocket Architecture**
- Socket.IO server for binary + text streaming
- Channels: `room:assessment:{sessionId}`
- Message types:
  - `code.update` — real-time code diff as candidate types
  - `evaluation.progress` — AI evaluation streaming
  - `reviewer.annotation` — inline comment at line/column
  - `reviewer.override` — manual score adjustment
  - `session.presence` — who's in the room

**Reviewer UI**
- Overlay mode on the center panel
- Click any line to leave annotation
- Annotations appear as ghosted comments linked to line numbers
- AI evaluation can be manually overridden (with audit trail)
- Reviewer can trigger "Go Harder" manually

**Permissions**
- Candidate: read/write own code, read annotations, read evaluation
- Reviewer: read code, write annotations, override scores, trigger escalation
- Observer: read-only (for training/demo)

### Subtasks
1. Install Socket.IO on backend and frontend
2. Create room management service (create, join, leave, destroy)
3. Implement code streaming with OT/CRDT for conflict resolution
4. Build annotation system (line-linked comments)
5. Create reviewer score override with audit trail
6. Build presence indicators
7. Write E2E test: candidate + reviewer simultaneous session

---

## Feature 10: Result Certification & Badge System

### Story
**As a** candidate who completed DevAscent assessments,  
**I want** a verifiable digital credential proving my engineering level,  
**So that** I can share it on LinkedIn, my portfolio, or with potential employers.

### Acceptance Criteria

**Credential Format**
- JSON-LD Verifiable Credential (W3C VC 2.0)
- Cryptographic signature using Ed25519
- On-chain anchor (optional, via Ethereum Attestation Service)

```json
{
  "@context": ["https://www.w3.org/ns/credentials/v2"],
  "type": ["VerifiableCredential", "DevAscentCredential"],
  "issuer": "did:web:devascent.dev",
  "credentialSubject": {
    "id": "did:ethr:0x...",
    "level": "SYSTEM_DESIGNER",
    "skillsMatrix": { "async_flows": 92, "connection_pooling": 88 },
    "completedChallenges": 12,
    "escalationsSurvived": 5,
    "issuedAt": "2026-06-23T00:00:00Z"
  }
}
```

**Verification**
- Public verifier page: `devascent.dev/verify/{credentialId}`
- QR code on badge linking to verifier
- Revocation list (can revoke if credential abused)
- LinkedIn integration (Open Badge 3.0 compatible)

**Badge Tiers & Visuals**
| Level | Badge | Requirements |
|-------|-------|-------------|
| BASELINE | Bronze ring | 3 challenges completed |
| SYSTEM_DESIGNER | Silver ring | 8 challenges, 2 escalations |
| TOP_1_PERCENT | Gold ring | 15 challenges, 5 escalations |
| ARCHITECT | Platinum ring | 25 challenges, all categories ≥80 |
| DISTINGUISHED | Diamond ring | 40 challenges, peer-reviewed |

### Subtasks
1. Generate DID and Ed25519 keypair for issuer
2. Implement VC issuance endpoint
3. Build public verifier page
4. Create badge SVG/PNG generator
5. Implement revocation list management
6. Build LinkedIn share integration
7. Add on-chain attestation (EAS) integration

---

## Feature 11: CI/CD Integration (GitHub Actions + Webhook Assessment)

### Story
**As a** hiring manager,  
**I want** to trigger a DevAscent assessment directly from a GitHub pull request or CI pipeline,  
**So that** I can include automated skill evaluation as part of my technical interview funnel.

### Acceptance Criteria

**GitHub Integration**
- GitHub App with `pull_request` and `check_run` permissions
- Trigger: comment `/devascent-assess` on a PR
  - Bot clones the PR, runs it through the sandbox
  - Posts results as a Check Run with score, feedback, and skill breakdown
- Trigger: push to `devascent/*` branch
  - Runs full assessment suite (5 challenges)
  - Posts summary as PR comment

**API-Driven Assessment**
```bash
# Trigger assessment programmatically
curl -X POST https://api.devascent.dev/v1/assessments \
  -H "Authorization: Bearer $DEVASCENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate": { "email": "candidate@company.com", "github": "user" },
    "challengeSet": "backend-systems",
    "callbackUrl": "https://company.com/webhook/dev-ascent"
  }'
```

**Webhook Events**
- `assessment.started`
- `assessment.challenge_completed`
- `assessment.level_changed`
- `assessment.completed`
- `assessment.failed`

### Subtasks
1. Build GitHub App with required permissions
2. Implement comment-trigger parser (`/devascent-assess`)
3. Create Check Run integration (post results as GitHub checks)
4. Build webhook dispatch system
5. Create CI/CD blueprint templates (GitHub Actions YAML)
6. Write docs for programmatic API usage

---

## Feature 12: Admin Analytics & Observability Dashboard

### Story
**As a** platform admin,  
**I want** comprehensive dashboards showing system health, user engagement, assessment throughput, and model performance,  
**So that** I can operate the platform at scale and debug issues quickly.

### Acceptance Criteria

**System Metrics**
- Queue depth (BullMQ): waiting, active, completed, failed
- Worker CPU/memory per Railway instance
- LLM latency p50/p95/p99 per model
- Sandbox execution time distribution
- API error rate by endpoint
- Active SSE connections

**Business Metrics**
- Daily active assessors
- Challenges completed per day
- Average score per skill category (across all users)
- Level distribution pie chart
- Escalation success rate
- Time-to-completion per level

**Alerting**
- Queue depth > 100 → warn
- Worker crash → alert
- LLM error rate > 5% → alert + auto-fallback
- Sandbox escape attempt detected → critical alert
- No completed assessments in 1 hour → warn (sanity check)

**Tech Stack**
- Prometheus for metrics collection
- Grafana for dashboards
- Pino for structured JSON logging
- OpenTelemetry for distributed tracing across: web → queue → worker → LLM

### Subtasks
1. Install Prometheus client and expose `/metrics` endpoint
2. Create Grafana dashboards (system + business)
3. Implement structured logging with Pino + request ID propagation
4. Add OpenTelemetry spans for: API request, queue job, LLM call, sandbox exec
5. Configure alerting rules in Alertmanager
6. Build admin-only analytics UI (React + recharts)

---

## Feature 13: Onboarding Wizard & Guided First Assessment

### Story
**As a** first-time user,  
**I want** a guided onboarding experience that calibrates my starting level before throwing me into a challenge,  
**So that** I don't get overwhelmed by a challenge that's too hard or bored by one that's too easy.

### Acceptance Criteria

**Onboarding Flow**
1. **Welcome screen** — brand intro, what DevAscent is, estimated time commitment
2. **Skill self-assessment** — rate yourself 1-10 on 8 dimensions (honesty-prompted)
3. **Quick benchmark** — 1 warm-up challenge (easy), scored but not level-determining
4. **Calibration** — system compares self-assessment vs benchmark score:
   - Overconfident (self-rate high, score low) → start 1 level lower, gentle nudge
   - Underconfident (self-rate low, score high) → start at actual level, confidence boost
   - Aligned → start at calibrated level
5. **Workspace tour** — "this is the challenge panel, this is where you code, this is your skills radar"
6. **First challenge start** — auto-triggered at calibrated level

**Calibration Algorithm**
```
calibratedLevel = IF benchmarkScore >= 85 AND selfAssessment.avg >= 7
  THEN MIN(selfAssessmentLevel, TOP_1_PERCENT)
  ELSE IF benchmarkScore >= 70
  THEN SYSTEM_DESIGNER
  ELSE BASELINE
```

### Subtasks
1. Design onboarding screen sequence (Stitch MCP)
2. Build self-assessment form (8 sliders + optional notes)
3. Implement benchmark challenge (pre-seeded, static)
4. Build calibration algorithm
5. Create workspace tour overlay (step-by-step tooltips)
6. Write A/B test framework for onboarding variants

---

---

# HERMES FORKING STRATEGY

## What We Keep (Hermes provides these for free)

| Capability | Hermes Module | DevAscent Use |
|-----------|--------------|---------------|
| **Agent loop** | `agent/` | Core assessment engine execution context |
| **Provider system** | `providers/` | LLM routing for evaluation, generation, embedding |
| **Memory system** | `hermes_state.py`, FTS5, Honcho | User profile, skill history, session continuity |
| **Skills system** | `skills/` | Reused as "assessment skills matrix" storage |
| **MCP integration** | `acp_adapter/`, `acp_registry/` | Stitch MCP UI connection + sandbox MCP |
| **Gateway** | `gateway/` | SSE endpoint, WebSocket for real-time eval |
| **Docker** | `docker/`, `Dockerfile` | Base Docker config, extend for sandbox + worker |
| **Config system** | `cli-config.yaml.example` | Assessment configuration (providers, timeouts, etc.) |
| **Web UI** | `web/` (TypeScript) | Base frontend — add Stitch panels on top |
| **TUI** | `ui-tui/` | Optional CLI assessment mode |
| **Cron** | `cron/` | Scheduled skill matrix decay, weekly reports |
| **Logging** | `hermes_logging.py` | Structured logging backbone |
| **Testing** | `tests/`, `scripts/run_tests.sh` | Test harness |

## What We Build (DevAscent-specific additions)

```
hermes-agent/                          ← Forked repo
├── devascent/                         ← NEW: DevAscent package
│   ├── assessment/
│   │   ├── state_graph.py             ← LangGraph state machine
│   │   ├── nodes/
│   │   │   ├── initialize.py
│   │   │   ├── evaluate.py
│   │   │   ├── update_skills.py
│   │   │   ├── determine_next.py
│   │   │   └── escalate.py
│   │   ├── evaluator/
│   │   │   ├── rubric.py
│   │   │   ├── sandbox_executor.py    ← gVisor integration
│   │   │   └── constraint_validator.py
│   │   └── router.py
│   ├── rag/
│   │   ├── embedder.py                ← Embedding generation
│   │   ├── retriever.py               ← pgvector similarity search
│   │   └── seed_data.py               ← 15+ challenge seed
│   ├── queue/
│   │   ├── worker.py                  ← BullMQ worker (Python via redis-py)
│   │   └── events.py                  ← SSE event emitter
│   ├── cert/
│   │   ├── issuer.py                  ← VC issuance
│   │   └── verifier.py                ← Public verification
│   └── analytics/
│       ├── metrics.py                 ← Prometheus exporters
│       └── tracing.py                 ← OpenTelemetry
├── web/                               ← EXTEND: add Stitch UI panels
│   ├── components/
│   │   ├── assessment/                ← Assessment workspace panels
│   │   │   ├── ChallengePanel.tsx
│   │   │   ├── CodeReviewStream.tsx
│   │   │   ├── SkillsRadarMap.tsx
│   │   │   ├── SkillBarMeter.tsx
│   │   │   ├── LevelBadge.tsx
│   │   │   └── EscalationGauge.tsx
│   │   └── admin/                     ← Admin dashboards
│   └── pages/
│       ├── assess/                    ← Assessment workspace route
│       └── admin/                     ← Admin dashboard route
├── migrations/                        ← NEW: PostgreSQL migrations
│   ├── 001_enable_pgvector.sql
│   ├── 002_create_challenges.sql
│   ├── 003_create_assessments.sql
│   └── 004_create_organizations.sql
├── Dockerfile.worker                  ← NEW: Railway worker image
├── railway.toml                       ← NEW: Railway config
└── stitch/                            ← NEW: Stitch MCP project exports
    └── design-system/
```

## Fork & Rebrand Plan

1. **Fork** `NousResearch/hermes-agent` → `DevAscent/hermes-agent` (private monorepo)
2. **Rename** all `hermes` references → `devascent` in:
   - CLI command (`hermes → devascent`)
   - Config dir (`~/.hermes → ~/.devascent`)
   - Environment variables (`HERMES_ → DEVASCENT_`)
   - Python package (`import hermes → import devascent`)
3. **Strip** unused features:
   - Remove messaging gateways (Telegram, Discord, Slack, Signal, WhatsApp) — not needed for assessment platform
   - Remove image generation tools
   - Remove voice/TTS
   - Remove browser-use tools
   - Keep: agent loop, providers, skills, memory, MCP, Docker, cron, tests
4. **Add** DevAscent packages as shown above
5. **Deploy** on Railway with:
   - Web server (Express + SSE) ← reuses Hermes gateway
   - Worker (BullMQ) ← new
   - PostgreSQL + pgvector ← new
   - Redis ← reuses Hermes Redis config
6. **CI/CD**: GitHub Actions for lint, test, build, deploy-prod

---

## Implementation Order (Priority Sequencing)

```
PHASE 1 — Core Engine (Week 1-2)
├── Fork Hermes, strip unused modules
├── Feature 1: LangGraph state machine
├── Feature 8: LLM provider layer
└── Feature 2: pgvector + seed data

PHASE 2 — Assessment Pipeline (Week 3-4)
├── Feature 6: Sandbox executor
├── Feature 5: BullMQ + SSE
├── Feature 3: Go Harder escalation engine
└── Feature 13: Onboarding wizard

PHASE 3 — UI & UX (Week 5-6)
├── Feature 4: Stitch MCP workspace
├── Feature 9: Real-time collaboration
└── Feature 10: Certification & badges

PHASE 4 — Enterprise (Week 7-8)
├── Feature 7: Multi-tenant / orgs
├── Feature 11: CI/CD GitHub integration
└── Feature 12: Admin analytics

PHASE 5 — Launch (Week 9)
├── Load testing (k6, 1000 concurrent users)
├── Security audit (pen test, dependency scan)
├── Documentation (API docs, user guide, deployment guide)
└── Production deploy on Railway
```

---

## Total Story Count: 13 Features

| # | Feature | Priority |
|---|---------|----------|
| 1 | LangGraph Assessment State Machine | P0 — Core |
| 2 | Vector-Driven RAG Pipeline | P0 — Core |
| 3 | Go Harder Escalation Engine | P0 — Core |
| 4 | Apple-Minimalist Workspace (Stitch) | P0 — Core |
| 5 | Async Eval Pipeline (BullMQ) | P0 — Core |
| 6 | Secure Code Sandbox | P0 — Security |
| 7 | Multi-Tenant Auth & Orgs | P1 — Enterprise |
| 8 | LLM Provider Abstraction | P0 — Infra |
| 9 | Real-Time Collaboration | P2 — Enhancement |
| 10 | Certification & Badges | P1 — Product |
| 11 | CI/CD GitHub Integration | P1 — Integration |
| 12 | Admin Analytics | P1 — Operations |
| 13 | Onboarding Wizard | P0 — UX |
