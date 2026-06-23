"""Assessment API routes — session management and submission."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["assessment"])


@router.post("/start")
async def start_assessment(user_id: str | None = None):
    """Initialize a new assessment session."""
    session_id = str(uuid.uuid4())
    return {
        "sessionId": session_id,
        "currentLevel": "BASELINE",
        "skillsMatrix": {},
        "startedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{session_id}/submit")
async def submit_code(session_id: str, challenge_id: str, code: str, language: str):
    """Submit code for evaluation. Returns 202 with job tracking info."""
    job_id = str(uuid.uuid4())
    return {
        "jobId": job_id,
        "streamUrl": f"/api/assessment/stream/{job_id}",
        "status": "queued",
    }


@router.get("/{session_id}/state")
async def get_state(session_id: str):
    """Get current assessment state including skills matrix and history."""
    return {
        "sessionId": session_id,
        "currentLevel": "BASELINE",
        "skillsMatrix": {},
        "escalationDepth": 0,
        "evaluationHistory": [],
    }


@router.get("/{session_id}/next")
async def get_next_challenge(session_id: str):
    """Get the next challenge for this session."""
    raise HTTPException(status_code=501, detail="Challenge retrieval not yet implemented")
