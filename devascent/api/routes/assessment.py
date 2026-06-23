"""Assessment API routes — LangGraph state machine integration."""
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
from devascent.assessment.state_graph import get_graph

router = APIRouter(tags=["assessment"])


@router.post("/start", response_model=StartAssessmentResponse)
async def start_assessment(body: StartAssessmentRequest):
    """Initialize a new assessment session via LangGraph."""
    graph = get_graph()
    session_id = str(uuid.uuid4())
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


@router.post("/{session_id}/submit", response_model=SubmitCodeResponse)
async def submit_code(session_id: str, body: SubmitCodeRequest):
    """Submit code for evaluation through the LangGraph pipeline."""
    graph = get_graph()
    job_id = str(uuid.uuid4())

    config = {"configurable": {"thread_id": session_id}}

    # Load existing state from checkpointer
    try:
        state_snapshot = await graph.aget_state(config)
        if state_snapshot.values:
            current_state = state_snapshot.values
        else:
            current_state = {}
    except Exception:
        current_state = {}

    # Build update with the submission
    update: DevAscentState = {
        "active_challenge_id": body.challenge_id,
        "submitted_code": body.code,
        "submitted_language": body.language,
    }

    merged = {**current_state, **update}

    # Run evaluation through the graph — this triggers:
    # evaluate → update_skills → determine_next → [escalate | present_challenge | END]
    result = await graph.ainvoke(merged, config)

    return SubmitCodeResponse(
        job_id=job_id,
        stream_url=f"/api/assessment/stream/{job_id}",
        status="completed" if result.get("next_action") == "flag_review" else "evaluated",
    )


@router.get("/{session_id}/state", response_model=AssessmentStateResponse)
async def get_state(session_id: str):
    """Get current assessment state from LangGraph checkpointer."""
    graph = get_graph()
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


@router.get("/{session_id}/next")
async def get_next_challenge(session_id: str):
    """Advance to the next challenge."""
    graph = get_graph()
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
