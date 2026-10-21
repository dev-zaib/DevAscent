"""Assessment API routes — with mock fallback for demo without LangGraph."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from devascent.assessment.state import (
    StartAssessmentRequest,
    StartAssessmentResponse,
    SubmitCodeRequest,
    SubmitCodeResponse,
    AssessmentStateResponse,
    DevAscentState,
    make_initial_state,
)
from devascent.rag.seed_data import SEED_CHALLENGES

router = APIRouter(tags=["assessment"])

# In-memory session store for demo (when LangGraph/PostgreSQL unavailable)
_demo_sessions: dict[str, dict] = {}

# Decay-weighted skill update (matches the LangGraph UpdateSkillsMatrix node).
_DECAY, _NEW = 0.7, 0.3


def _get_graph():
    """Lazy-load LangGraph to avoid import errors when deps not installed."""
    try:
        from devascent.assessment.state_graph import get_graph
        return get_graph()
    except ImportError:
        return None


def _route_action(score: float, level: str, depth: int) -> str:
    if score >= 85:
        return "escalate" if (level == "BASELINE" and depth < 3) else "advance_level"
    if score >= 70:
        return "keep_level"
    if score >= 40:
        return "reinforce"
    return "flag_review"


def _mock_eval(challenge: dict) -> dict:
    """Deterministic offline evaluation when DeepSeek is unavailable."""
    rubric = challenge.get("rubric", {}) or {"code_quality": {"weight": 100}}
    # Spread scores so the radar looks alive even offline.
    base = [82, 75, 68, 88, 71, 79]
    breakdown = {
        skill: float(base[i % len(base)]) for i, skill in enumerate(rubric.keys())
    }
    total_w = sum((rubric.get(s, {}) or {}).get("weight", 1) for s in breakdown) or 1
    score = round(
        sum(breakdown[s] * (rubric.get(s, {}) or {}).get("weight", 1) for s in breakdown) / total_w,
        2,
    )
    return {
        "score": score,
        "rubric_breakdown": breakdown,
        "ai_feedback": (
            "Offline demo evaluation. Set DEEPSEEK_API_KEY for real AI grading. "
            "Solid structure; tighten edge-case handling and add failure-path tests."
        ),
        "strengths": ["Readable structure"],
        "gaps": ["Edge cases", "Failure paths"],
        "provider": "mock",
    }


def _evaluate(code: str, language: str, challenge: dict) -> dict:
    """Real DeepSeek evaluation with graceful fallback to the mock grader."""
    try:
        from devascent.llm import deepseek

        if deepseek.is_configured():
            return deepseek.evaluate_code(code, language, challenge)
    except Exception:
        pass
    return _mock_eval(challenge)


def _demo_evaluate(code: str, language: str) -> dict:
    """Legacy shim retained for compatibility (unused by submit path)."""
    return {
        "score": 78.0,
        "rubric_breakdown": {
            "rate_limiting": 82,
            "api_design": 75,
            "error_handling": 88,
            "code_quality": 70,
        },
        "ai_feedback": "Solid implementation. Consider adding Redis for distributed rate limiting.",
        "next_action": "keep_level",
        "skills_matrix": {
            "rate_limiting": 82,
            "api_design": 75,
            "error_handling": 88,
            "code_quality": 70,
        },
        "escalation_depth": 0,
        "challenge": SEED_CHALLENGES[1] if len(SEED_CHALLENGES) > 1 else None,
    }


def _mock_lesson(challenge: dict, language: str) -> dict:
    """Offline lesson when DeepSeek is unavailable."""
    skills = list((challenge.get("rubric", {}) or {}).keys())
    return {
        "concept": (
            f"This challenge tests: {', '.join(skills) or 'core engineering'}. "
            "Break it into the smallest correct version first, then add the production concerns."
        ),
        "key_points": challenge.get("hints", []) or ["Start with the happy path", "Then handle failures"],
        "approach_steps": [
            "Restate the requirements in your own words.",
            "Write the simplest version that passes one case.",
            "Add edge cases and failure handling.",
            "Add the production constraints in the rubric.",
        ],
        "common_mistakes": ["Skipping edge cases", "Ignoring failure paths", "No tests"],
        "starter_code": f"// {language} scaffold\n// TODO: implement {challenge.get('title','the solution')}\n",
        "study_terms": challenge.get("target_skills", []) or [],
        "provider": "mock",
    }


def _lesson_for(challenge: dict, language: str) -> dict:
    try:
        from devascent.llm import deepseek
        if deepseek.is_configured():
            return deepseek.teach(challenge, language)
    except Exception:
        pass
    return _mock_lesson(challenge, language)


@router.post("/{session_id}/learn")
async def learn_challenge(session_id: str, body: dict | None = None):
    """Generate a guided lesson for the session's current challenge."""
    language = (body or {}).get("language", "typescript")
    session = _demo_sessions.get(session_id)
    challenge = session.get("challenge_data") if session else None
    if not challenge:
        # Fall back to the first seed challenge so /learn works pre-start too.
        challenge = SEED_CHALLENGES[0]
    return {"challenge_id": challenge.get("title", ""), "lesson": _lesson_for(challenge, language)}


@router.post("/start", response_model=StartAssessmentResponse)
async def start_assessment(body: StartAssessmentRequest):
    """Initialize a new assessment session."""
    graph = _get_graph()
    session_id = str(uuid.uuid4())

    if graph:
        initial_state = make_initial_state(body.user_id)
        config = {"configurable": {"thread_id": session_id}}
        result = await graph.ainvoke(initial_state, config)
        challenge = result.get("active_challenge_data") or {}
        return StartAssessmentResponse(
            session_id=session_id,
            current_level=result.get("current_level", "BASELINE"),
            skills_matrix=result.get("skills_matrix", {}),
            challenge_id=result.get("active_challenge_id", ""),
            challenge_data=challenge if challenge else None,
        )

    # Demo fallback — start on the gentlest beginner challenge.
    challenge = SEED_CHALLENGES[0]
    _demo_sessions[session_id] = {
        "user_id": body.user_id,
        "current_level": "BASELINE",
        "skills_matrix": {},
        "escalation_depth": 0,
        "challenge_attempt": 1,
        "challenge_idx": 0,
        "evaluation_history": [],
        "active_challenge_id": challenge["title"],
        "challenge_data": challenge,
        "next_action": "",
    }
    return StartAssessmentResponse(
        session_id=session_id,
        current_level="BASELINE",
        skills_matrix={},
        challenge_id=challenge["title"],
        challenge_data=challenge,
    )


@router.post("/{session_id}/submit", response_model=SubmitCodeResponse)
async def submit_code(session_id: str, body: SubmitCodeRequest):
    """Submit code for evaluation."""
    graph = _get_graph()
    job_id = str(uuid.uuid4())

    if graph:
        config = {"configurable": {"thread_id": session_id}}
        try:
            state_snapshot = await graph.aget_state(config)
            current_state = state_snapshot.values if state_snapshot.values else {}
        except Exception:
            current_state = {}
        update: DevAscentState = {
            "active_challenge_id": body.challenge_id,
            "submitted_code": body.code,
            "submitted_language": body.language,
        }
        merged = {**current_state, **update}
        result = await graph.ainvoke(merged, config)
        return SubmitCodeResponse(
            job_id=job_id,
            stream_url=f"/api/assessment/stream/{job_id}",
            status="completed" if result.get("next_action") == "flag_review" else "evaluated",
        )

    # Demo fallback — real DeepSeek evaluation (mock when no key), persisted
    # to the durable learning journal so the coach endpoints reflect it.
    session = _demo_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    challenge = session.get("challenge_data") or {}
    result = _evaluate(body.code, body.language, challenge)

    # Decay-weighted skill matrix update + per-skill deltas.
    skills = dict(session.get("skills_matrix", {}))
    deltas: dict[str, float] = {}
    for skill, sc in result["rubric_breakdown"].items():
        if skill in skills:
            new = round(skills[skill] * _DECAY + sc * _NEW, 2)
        else:
            new = round(float(sc), 2)  # first observation seeds at full value
        old = skills.get(skill, 0.0)
        skills[skill] = new
        deltas[skill] = round(new - old, 2)
    session["skills_matrix"] = skills

    level = session.get("current_level", "BASELINE")
    depth = session.get("escalation_depth", 0)
    next_action = _route_action(result["score"], level, depth)
    session["next_action"] = next_action

    ts = datetime.now(timezone.utc).isoformat()
    session["evaluation_history"].append({
        "challenge_id": body.challenge_id,
        "score": result["score"],
        "rubric_breakdown": result["rubric_breakdown"],
        "ai_feedback": result["ai_feedback"],
        "timestamp": ts,
    })

    # Bridge into the durable journal + cross-session memory (the silo fix).
    try:
        from devascent.coach.journal import JournalEntry, LearningJournal
        from devascent.coach.coach import build_coach_report
        from devascent.coach.memory_bridge import write_progress_memory

        user_id = session.get("user_id") or "anonymous"
        journal = LearningJournal(user_id)
        journal.append(JournalEntry(
            challenge_id=body.challenge_id,
            level=level,
            score=float(result["score"]),
            rubric_scores=result["rubric_breakdown"],
            skill_deltas=deltas,
            ai_feedback=result["ai_feedback"],
            escalation_depth=depth,
            timestamp=ts,
        ))
        report = build_coach_report(user_id, journal.read_all(), skills, level=level)
        write_progress_memory(report)
    except Exception:
        pass

    return SubmitCodeResponse(
        job_id=job_id,
        stream_url=f"/api/assessment/stream/{job_id}",
        status="evaluated",
    )


@router.get("/{session_id}/state", response_model=AssessmentStateResponse)
async def get_state(session_id: str):
    """Get current assessment state."""
    graph = _get_graph()

    if graph:
        config = {"configurable": {"thread_id": session_id}}
        try:
            state_snapshot = await graph.aget_state(config)
            if not state_snapshot or not state_snapshot.values:
                raise HTTPException(status_code=404, detail="Session not found")
            state = state_snapshot.values
            return AssessmentStateResponse(
                session_id=session_id,
                current_level=state.get("current_level", "BASELINE"),
                skills_matrix=state.get("skills_matrix", {}),
                escalation_depth=state.get("escalation_depth", 0),
                challenge_attempt=state.get("challenge_attempt", 0),
                evaluation_history=state.get("evaluation_history", []),
                next_action=state.get("next_action"),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Demo fallback
    session = _demo_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return AssessmentStateResponse(
        session_id=session_id,
        current_level=session["current_level"],
        skills_matrix=session["skills_matrix"],
        escalation_depth=session["escalation_depth"],
        challenge_attempt=session["challenge_attempt"],
        evaluation_history=session.get("evaluation_history", []),
        next_action=session.get("next_action"),
    )


@router.get("/{session_id}/next")
async def get_next_challenge(session_id: str):
    """Advance to the next challenge."""
    graph = _get_graph()

    if graph:
        config = {"configurable": {"thread_id": session_id}}
        try:
            state_snapshot = await graph.aget_state(config)
            if not state_snapshot or not state_snapshot.values:
                raise HTTPException(status_code=404, detail="Session not found")
            state = state_snapshot.values
            state["submitted_code"] = ""
            state["submitted_language"] = ""
            result = await graph.ainvoke(state, config)
            challenge = result.get("active_challenge_data") or {}
            return {
                "sessionId": session_id,
                "challengeId": result.get("active_challenge_id"),
                "challenge": challenge,
                "nextAction": result.get("next_action", ""),
                "currentLevel": result.get("current_level"),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Demo fallback
    session = _demo_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Walk the ordered catalog (beginner → enterprise) without repeating.
    idx = (session.get("challenge_idx", 0) + 1) % len(SEED_CHALLENGES)
    session["challenge_idx"] = idx
    next_challenge = SEED_CHALLENGES[idx]
    session["active_challenge_id"] = next_challenge["title"]
    session["challenge_data"] = next_challenge
    session["challenge_attempt"] += 1

    return {
        "sessionId": session_id,
        "challengeId": next_challenge["title"],
        "challenge": next_challenge,
        "nextAction": "keep_level",
        "currentLevel": session["current_level"],
    }
