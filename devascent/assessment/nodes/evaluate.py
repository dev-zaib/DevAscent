"""EvaluateSubmission node — scores user code against challenge rubric."""
from datetime import datetime, timezone
from devascent.assessment.state import DevAscentState, EvaluationLog
from devascent.assessment.evaluator.rubric import (
    RubricEngine,
    build_evaluation_prompt,
    parse_evaluation_response,
)


# Mock evaluation for when no LLM provider is available
MOCK_SCORES = {
    "rate_limiting": 82,
    "api_design": 75,
    "error_handling": 88,
    "code_quality": 70,
}


def evaluate_with_llm(challenge: dict, code: str, language: str) -> dict:
    """Run evaluation via LLM provider.

    In production, this calls OpenRouter/OpenAI/Anthropic with the
    evaluation prompt. For now, returns mock scores.
    """
    try:
        rubric = RubricEngine(challenge.get("rubric", {}))
        prompt = build_evaluation_prompt(challenge, code, language, rubric)

        # In production: call LLM provider here
        # from devascent.providers import get_provider
        # provider = get_provider("evaluation")
        # response = provider.chat(prompt)
        # result = parse_evaluation_response(response)

        # For now use mock scores
        total = rubric.compute_score(MOCK_SCORES)
        return {
            "scores": MOCK_SCORES,
            "feedback": {
                "rate_limiting": "Good use of sliding window pattern. Consider request bursting handling.",
                "api_design": "Clean proxy structure. Could add configurable upstream URL.",
                "error_handling": "Proper 429 response. Added helpful Retry-After header.",
                "code_quality": "Well-named functions. Could benefit from input validation.",
            },
            "overall_notes": "Solid implementation with good rate-limiting logic. Consider making the rate limit configurable.",
            "total": total,
        }
    except Exception:
        rubric = RubricEngine(challenge.get("rubric", {}))
        return {
            "scores": MOCK_SCORES,
            "feedback": {},
            "overall_notes": "Fallback evaluation — LLM unavailable.",
            "total": rubric.compute_score(MOCK_SCORES),
        }


def evaluate_submission(state: DevAscentState) -> dict:
    challenge = state.get("active_challenge_data") or {}
    challenge_id = state.get("active_challenge_id", "")

    # Get the latest submission code from state or use placeholder
    code = state.get("submitted_code", "")
    language = state.get("submitted_language", "typescript")

    if not code:
        return {"latest_score": 0.0}

    result = evaluate_with_llm(challenge, code, language)

    now = datetime.now(timezone.utc).isoformat()
    log_entry: EvaluationLog = {
        "challenge_id": challenge_id,
        "score": result["total"],
        "rubric_breakdown": result["scores"],
        "ai_feedback": result.get("overall_notes", ""),
        "constraints_applied": state.get("escalation_constraints", []),
        "timestamp": now,
    }

    history = list(state.get("evaluation_history", []))
    history.append(log_entry)

    return {
        "latest_score": result["total"],
        "evaluation_history": history,
        "last_evaluation_timestamp": now,
        "rubric_scores": result["scores"],
        "ai_feedback": result.get("overall_notes", ""),
    }
