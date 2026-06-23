"""LangGraph assessment state definition."""
from typing import TypedDict, NotRequired


class EvaluationLog(TypedDict):
    challenge_id: str
    score: float
    rubric_breakdown: dict[str, float]
    ai_feedback: str
    constraints_applied: list[str]
    timestamp: str


class DevAscentState(TypedDict):
    user_id: str
    current_level: str  # BASELINE | SYSTEM_DESIGNER | TOP_1_PERCENT | ARCHITECT
    skills_matrix: dict[str, float]
    active_challenge_id: str
    challenge_attempt: int
    evaluation_history: list[EvaluationLog]
    escalation_depth: int
    session_start_time: str
    last_evaluation_timestamp: str
