# DevAscent Skill Coach

The Coach is the layer that makes DevAscent **actually build skills** rather
than just score one-off submissions.

## The problem it fixes

Before this layer, the assessment engine was **siloed**. Each evaluation
updated the LangGraph `DevAscentState` and was checkpointed to Postgres —
but nothing fed back into a durable, cross-session skill-building loop. The
hermes core (which DevAscent forks) ships two assets that were going unused:

- **cross-session memory**, and
- a **self-improving skills system**.

The Coach reconnects the assessment to both.

## Architecture

```
EvaluateSubmission → UpdateSkillsMatrix → CoachProgress → DetermineNextStep
                                              │
                 ┌────────────────────────────┼─────────────────────────────┐
                 ▼                            ▼                              ▼
        LearningJournal (JSONL)      build_coach_report            memory_bridge
        durable, per-user        mastery / momentum / curriculum   hermes memory note
```

| Module | Responsibility | Pure? |
|--------|----------------|-------|
| `journal.py` | Append-only per-user JSONL of every evaluation | I/O only |
| `curriculum.py` | Per-skill stats, trend, **spaced repetition** (SM-2 style), ranked next-practice | ✅ pure |
| `coach.py` | `CoachReport` — overall mastery, momentum, strongest/weakest, milestones | ✅ pure |
| `memory_bridge.py` | Writes a hermes-format progress note + JSON snapshot | I/O only |
| `reminder.py` | Cron-ready daily practice nudge | thin CLI |

`now` is injectable everywhere time matters, so the engine is deterministic
and fully unit-testable with **no DB, Redis, langgraph, or agent runtime**.

## Spaced repetition

Each skill gets a review interval from `SR_INTERVALS` (1, 2, 4, 7, 14, 30, 60
days) indexed by its run of consecutive strong reps (score ≥ 70). Fragile
(<40) and developing (<70) skills get tightened intervals. A skill past its
window is flagged `due` and floated to the top of the curriculum.

## API

- `GET /api/coach/progress/{user_id}` — full coach report
- `GET /api/coach/curriculum/{user_id}?limit=5` — ranked practice items
- `GET /api/coach/history/{user_id}?limit=50` — recent journal entries

These read the journal directly and work even when LangGraph/Postgres are
offline.

## Daily habit (cron)

```
python -m devascent.coach.reminder <user_id>          # human-readable
python -m devascent.coach.reminder <user_id> --json   # for tooling
```

Schedule via the hermes cron subsystem for a daily skill-building nudge.

## Tests

```
PYTHONPATH=. .venv/bin/python tests/devascent/test_coach.py
```

11 unit tests, infra-free, also pytest-compatible.
