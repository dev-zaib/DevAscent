"""LangGraph assessment state with Pydantic validation."""
from typing import TypedDict, Annotated
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class EvaluationLog(TypedDict, total=False):
    challenge_id: str
    score: float
    rubric_breakdown: dict[str, float]
    ai_feedback: str
    constraints_applied: list[str]
    timestamp: str


class DevAscentState(TypedDict, total=False):
    user_id: str
    current_level: str
    skills_matrix: dict[str, float]
    active_challenge_id: str
    challenge_attempt: int
    evaluation_history: list[EvaluationLog]
    escalation_depth: int
    session_start_time: str
    last_evaluation_timestamp: str
    # Runtime fields (populated during graph execution)
    latest_score: float
    next_action: str
    active_challenge_data: dict | None
    submitted_code: str
    submitted_language: str
    rubric_scores: dict[str, float]
    ai_feedback: str
    escalation_constraints: list[str]
    # Coach fields (populated by the CoachProgress node)
    skill_deltas: dict[str, float]
    coach_report: dict | None
    curriculum: list[str]
    coach_error: str


# Pydantic models for API request/response validation

class StartAssessmentRequest(BaseModel):
    user_id: str = Field(..., description="User ID to start assessment for")


class StartAssessmentResponse(BaseModel):
    session_id: str
    current_level: str
    skills_matrix: dict[str, float]
    challenge_id: str
    challenge_data: dict | None = None


class SubmitCodeRequest(BaseModel):
    challenge_id: str = Field(..., description="Challenge being submitted against")
    code: str = Field(..., min_length=1, description="Submitted source code")
    language: str = Field(..., description="Programming language")


class SubmitCodeResponse(BaseModel):
    job_id: str
    stream_url: str
    status: str


class AssessmentStateResponse(BaseModel):
    session_id: str
    current_level: str
    skills_matrix: dict[str, float]
    escalation_depth: int
    challenge_attempt: int
    evaluation_history: list[dict]
    next_action: str | None = None


def make_initial_state(user_id: str) -> DevAscentState:
    return DevAscentState(
        user_id=user_id,
        current_level="BASELINE",
        skills_matrix={},
        active_challenge_id="",
        challenge_attempt=0,
        evaluation_history=[],
        escalation_depth=0,
        session_start_time=datetime.now(timezone.utc).isoformat(),
        last_evaluation_timestamp="",
        latest_score=0.0,
        next_action="",
        active_challenge_data=None,
        submitted_code="",
        submitted_language="",
        rubric_scores={},
        ai_feedback="",
        escalation_constraints=[],
    )
