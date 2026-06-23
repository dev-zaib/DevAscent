# P1-06: Assessment API OpenAPI Spec + FastAPI App

**Status:** ⬜ todo | **Depends on:** P1-04 | **Blocks:** P2-08

## AC
- [ ] FastAPI app scaffold at `devascent/api/app.py`
- [ ] OpenAPI 3.1 spec defines all assessment endpoints
- [ ] App mounts on existing Hermes web server (extends dashboard FastAPI)
- [ ] Health check endpoint: `GET /api/health`
- [ ] CORS configured for local dev
- [ ] Request/response Pydantic models defined

## Endpoints (from DEVASCENT_STORIES.md spec)
```
POST   /api/assessment/start          → 201 { sessionId, initialChallenge, skillsMatrix }
POST   /api/assessment/:id/submit     → 202 { jobId, streamUrl }
GET    /api/assessment/stream/:jobId  → SSE (text/event-stream)
GET    /api/assessment/:id/state      → 200 DevAscentState
GET    /api/assessment/:id/next       → 200 { challenge, ... }
POST   /api/assessment/:id/pause      → 200 { pausedAt }
POST   /api/assessment/:id/resume     → 200 { resumedAt }
GET    /api/health                    → 200 { status: "ok" }
```

## SSE Events
`progress`, `rubric`, `skills_update`, `complete`, `error` (with typed JSON payloads)