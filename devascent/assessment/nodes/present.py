"""PresentChallenge node — retrieves and presents next challenge."""
from datetime import datetime, timezone
from devascent.assessment.state import DevAscentState


DEFAULT_CHALLENGE = {
    "id": "challenge-baseline-001",
    "title": "Rate-Limited API Proxy",
    "description": (
        "Build a TypeScript API proxy that sits between a client and an "
        "external weather API. The proxy must enforce rate limiting — "
        "no more than 5 requests per second per client IP. Use an "
        "in-memory store (Map or object) for request counting. "
        "Return HTTP 429 when rate limit is exceeded."
    ),
    "difficulty": "easy",
    "target_skills": ["rate_limiting", "api_design"],
    "target_level": "BASELINE",
    "rubric": {
        "rate_limiting": {"weight": 40, "description": "Correct rate limiting logic"},
        "api_design": {"weight": 30, "description": "Clean proxy architecture"},
        "error_handling": {"weight": 20, "description": "Proper HTTP status codes"},
        "code_quality": {"weight": 10, "description": "Readable, well-structured code"},
    },
    "hints": [
        "Use a Map<string, number[]> to track request timestamps per client IP",
        "Clean up old entries periodically to avoid memory leaks",
    ],
}


def present_challenge(state: DevAscentState) -> dict:
    """Select and present the next challenge based on skills matrix.

    In production this calls the RAG retriever to find the best
    challenge matching the user's weak spots. For now, returns the
    default baseline challenge on first attempt.
    """
    challenge = DEFAULT_CHALLENGE

    state_update = {
        "active_challenge_id": challenge["id"],
        "active_challenge_data": challenge,
        "challenge_attempt": state.get("challenge_attempt", 0) + 1,
        "last_evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return state_update
