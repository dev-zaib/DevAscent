# Phase 2: LangGraph Assessment State Machine

**Status:** ⬜ todo | **Depends on:** Phase 1 | **Files:** `devascent/assessment/`

## P2-01: DevAscentState Typed Dict + Validation
**AC:** Define `DevAscentState` TypedDict in `devascent/assessment/state.py` with all fields from spec. Add Pydantic model for runtime validation. Fields: `userId`, `currentLevel`, `skillsMatrix`, `activeChallengeId`, `challengeAttempt`, `evaluationHistory`, `escalationDepth`.

## P2-02: LangGraph State Graph + PG Checkpointer
**AC:** Create `devascent/assessment/state_graph.py`. Build `StateGraph(DevAscentState)` with PG checkpointer using `langgraph-checkpoint-postgres`. Export `compile_assessment_graph()` → compiled graph. Test: graph compiles without errors.

## P2-03: InitializeAssessment Node
**AC:** Node reads user from DB (or creates new session). Seeds initial skills matrix (all 0). Sets `currentLevel = 'BASELINE'`. Stores state in PG checkpoint.

## P2-04: PresentChallenge Node
**AC:** Node retrieves challenge via `ChallengeRetriever` (P3-04). Sets `activeChallengeId`. Returns challenge data for frontend. Emits SSE `progress` event.

## P2-05: EvaluateSubmission Node + Rubric Engine
**AC:** Node runs submitted code through `SandboxExecutor` (P4-02) → captures output. Sends code + output + rubric to LLM for scoring. `rubric.py` defines scoring dimensions per challenge. Returns `score` + `rubricBreakdown` + `aiFeedback`. Emits SSE `rubric` events per dimension.

## P2-06: UpdateSkillsMatrix Node
**AC:** Weighted recalculation: `new_score = old * 0.7 + eval_score * 0.3`. Only updates dimensions present in the challenge rubric. Triggers `UserWeakSpot` embedding regeneration (P3-05). Emits SSE `skills_update` event.

## P2-07: DetermineNextStep Router + Conditional Edges
**AC:** Implement routing logic in `devascent/assessment/router.py`:
```
score >= 85 AND level == BASELINE AND escalationDepth < 3 → EscalateChallenge
score >= 85 AND (level != BASELINE OR escalationDepth >= 3) → LevelAdvance  
score >= 70 → keep level, serve variant
score < 70 → reinforce weak dimension
score < 40 → flag human review
```

## P2-08: Assessment API Endpoints
**AC:** Wire LangGraph graph to FastAPI routes in `devascent/api/routes/assessment.py`. Each endpoint invokes graph node and returns state snapshot. SSE stream endpoint uses `sse-starlette`.