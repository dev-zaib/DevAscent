"""Post-escalation constraint validator.

After a challenge has been escalated (Go Harder), the evaluator
verifies that the user's solution incorporates the new constraints.
Missing constraints result in automatic score penalties.
"""
import re

MISSING_CONSTRAINT_PENALTY = 15  # Points deducted per missing constraint

CONSTRAINT_PATTERNS = {
    "redis": {
        "regex": r"(?:redis|ioredis|createClient|Redis\.)",
        "description": "Redis integration required",
    },
    "circuit_breaker": {
        "regex": r"(?:circuit.?breaker|CircuitBreaker|breaker\s*=|half.?open)",
        "description": "Circuit breaker pattern required",
    },
    "row_virtualization": {
        "regex": r"(?:virtualiz|window(?:ing)?\s*(?:scroll|render)|react-virtual|tanstack.*virtual|useVirtualizer)",
        "description": "Row/Window virtualization required",
    },
    "async_queue": {
        "regex": r"(?:bullmq|bull\s|Queue\s*\(|async\s*queue|task.?queue)",
        "description": "Async task queue required",
    },
    "semantic_cache": {
        "regex": r"(?:semantic\s*cach|embedding.*cache|cosine.*similar)",
        "description": "Semantic caching layer required",
    },
    "lru_cache": {
        "regex": r"(?:lru|LRU|LRUCache|least.?recently.?used)",
        "description": "LRU cache fallback required",
    },
    "graceful_shutdown": {
        "regex": r"(?:SIGTERM|graceful.*shutdown|server\.close|drain.*connect)",
        "description": "Graceful shutdown required",
    },
    "dead_letter": {
        "regex": r"(?:dead.?letter|DLQ|dead_letter_queue)",
        "description": "Dead letter queue required",
    },
    "hmac_signature": {
        "regex": r"(?:hmac|HMAC|createHmac|signature.*verif)",
        "description": "HMAC request signature validation required",
    },
    "region_aware": {
        "regex": r"(?:region|multi.?region|REGION\b|region.?aware)",
        "description": "Multi-region awareness required",
    },
}


def validate_constraints(code: str, constraints: list[str]) -> dict:
    """Check if escalation constraints are satisfied in the submitted code.

    Args:
        code: Submitted source code
        constraints: List of constraint descriptions from escalation

    Returns:
        dict with:
          - violations: list of missing constraint descriptions
          - penalty: total points to deduct
          - satisfied: list of constraint keys that passed
    """
    violations = []
    satisfied = []

    for constraint in constraints:
        constraint_lower = constraint.lower()

        matched = False
        for key, pattern in CONSTRAINT_PATTERNS.items():
            if key in constraint_lower:
                if re.search(pattern["regex"], code, re.IGNORECASE):
                    satisfied.append(key)
                    matched = True
                else:
                    violations.append(pattern["description"])
                    matched = True
                break

        if not matched:
            violations.append(f"Unrecognized constraint: {constraint}")

    penalty = len(violations) * MISSING_CONSTRAINT_PENALTY

    return {
        "violations": violations,
        "penalty": penalty,
        "satisfied": satisfied,
    }
