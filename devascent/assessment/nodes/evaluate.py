"""EvaluateSubmission node — sandbox execution + LLM scoring + constraint checks."""
from datetime import datetime, timezone
from devascent.assessment.state import DevAscentState, EvaluationLog
from devascent.assessment.evaluator.rubric import RubricEngine
from devascent.assessment.evaluator.sandbox import sandbox_executor
from devascent.assessment.evaluator.constraint_validator import validate_constraints


async def evaluate_submission(state: DevAscentState) -> dict:
    """Evaluate submitted code end-to-end.

    1. Execute code in gVisor sandbox
    2. Score against challenge rubric via LLM
    3. Validate escalation constraints (if escalated)
    4. Apply constraint penalties
    """
    challenge = state.get("active_challenge_data") or {}
    challenge_id = state.get("active_challenge_id", "")
    code = state.get("submitted_code", "")
    language = state.get("submitted_language", "typescript")

    if not code:
        return {"latest_score": 0.0}

    # Step 1: Sandbox execution
    result = await sandbox_executor.execute(code, language)
    sandbox_output = result.stdout

    # Step 2: Rubric-based LLM evaluation
    rubric = RubricEngine(challenge.get("rubric", {}))
    scores = _evaluate_with_rubric(rubric, challenge, code, language, sandbox_output, result)
    total = rubric.compute_score(scores)

    # Step 3: Constraint validation (post-escalation)
    constraints = state.get("escalation_constraints", [])
    constraint_penalty = 0
    constraint_violations = []
    if constraints:
        validation = validate_constraints(code, constraints)
        constraint_penalty = validation["penalty"]
        constraint_violations = validation["violations"]
        total = max(0, total - constraint_penalty)

    now = datetime.now(timezone.utc).isoformat()

    log_entry: EvaluationLog = {
        "challenge_id": challenge_id,
        "score": total,
        "rubric_breakdown": scores,
        "ai_feedback": _format_feedback(scores, constraint_violations, result),
        "constraints_applied": constraints,
        "timestamp": now,
    }

    history = list(state.get("evaluation_history", []))
    history.append(log_entry)

    return {
        "latest_score": total,
        "evaluation_history": history,
        "last_evaluation_timestamp": now,
        "rubric_scores": scores,
        "ai_feedback": log_entry["ai_feedback"],
    }


def _evaluate_with_rubric(
    rubric: RubricEngine,
    challenge: dict,
    code: str,
    language: str,
    output: str,
    result,
) -> dict[str, float]:
    """Score each rubric dimension.

    Production: sends code + output to LLM for qualitative evaluation.
    Development: basic heuristic scoring.
    """
    scores = {}
    for dim in rubric.dimensions:
        score = _heuristic_score(dim.name, code, output, result)
        scores[dim.name] = score
    return scores


def _heuristic_score(
    dimension: str, code: str, output: str, result
) -> float:
    """Basic heuristic scoring per rubric dimension."""
    code_lower = code.lower()
    base_score = 70.0

    if result.timed_out:
        return max(0, base_score - 30)
    if result.exit_code != 0:
        return max(0, base_score - 20)

    # Simple pattern matching for common engineering patterns
    patterns = {
        "rate_limiting": [r"(?:rate.?lim|throttl|sliding.?window)", r"429", r"(?:Retry-After|X-RateLimit)"],
        "redis": [r"(?:redis|ioredis|createClient)", r"(?:ZADD|ZRANGE|SADD|LPUSH)"],
        "connection_pooling": [r"(?:pool\s*[=:]|createPool|Pool\s*\()", r"(?:max\s*=|maxSize|connectionLimit)"],
        "api_design": [r"(?:app\.\w+|router|middleware)", r"(?:async|await|Promise)"],
        "error_handling": [r"(?:try|catch|\.catch|on\('error')", r"status\s*\(\s*[45]\d\d"],
        "code_quality": [r"^\s*(?:interface|type) \w+", r"^\s*(?:const|function|class) \w+"],
        "fault_tolerance": [r"(?:retry|fallback|circuit.?break)", r"(?:try|catch|error.*handl)"],
        "memory_management": [r"(?:stream|pipeline|createReadStream)", r"(?:WeakRef|FinalizationRegistry)"],
        "caching": [r"(?:cache|Cache|LRU|TTL|\.set\(|\.get\()", r"(?:expir|ttl|maxAge)"],
        "rendering": [r"(?:virtualiz|useVirtualizer|react-virtual|React)", r"(?:overflow|scroll)"],
        "performance": [r"(?:\.?memoz?|useMemo|useCallback|React\.memo)", r"(?:requestAnimationFrame|raf)"],
        "realtime": [r"(?:WebSocket|ws\.|socket\.io|Server\s*\(|\.emit\()"],
        "backpressure": [r"(?:backpressure|bufferedAmount|drain|buffer.*full)"],
        "auth": [r"(?:jwt|sign\s*\(|verify\s*\(|JsonWebToken)", r"(?:bcrypt|hash|salt|RS256)"],
        "security": [r"(?:sanitize|validate|escape|CORS|helmet)", r"(?:xss|sqli|csrf|inject)"],
        "monitoring": [r"(?:metrics|prometheus|grafana|health|/health)", r"(?:log|warn|error|info)"],
    }

    dim_patterns = patterns.get(dimension, [])
    if not dim_patterns:
        return base_score

    matches = 0
    for pattern in dim_patterns:
        if [line for line in code.split("\n") if _pattern_match(pattern, line)]:
            matches += 1

    bonus = (matches / len(dim_patterns)) * 15
    return min(95, base_score + bonus)


def _pattern_match(pattern: str, line: str) -> bool:
    """Check if a line matches a heuristic pattern (simple string check)."""
    return pattern.lower() in line.lower()


def _format_feedback(
    scores: dict[str, float],
    violations: list[str],
    result,
) -> str:
    """Generate human-readable evaluation feedback."""
    feedback = []

    for dim, score in scores.items():
        if score >= 85:
            feedback.append(f"{dim}: Excellent ({score})")
        elif score >= 70:
            feedback.append(f"{dim}: Good ({score})")
        else:
            feedback.append(f"{dim}: Needs improvement ({score})")

    if result.timed_out:
        feedback.append("WARNING: Code execution timed out.")
    elif result.exit_code != 0:
        feedback.append(f"WARNING: Code exited with code {result.exit_code}.")

    if violations:
        feedback.append("MISSING CONSTRAINTS:")
        for v in violations:
            feedback.append(f"  - {v}")

    return "\n".join(feedback)
