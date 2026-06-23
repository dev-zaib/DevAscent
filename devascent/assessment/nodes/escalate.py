"""EscalateChallenge node — injects production chaos constraints."""
from devascent.assessment.state import DevAscentState


ESCALATION_CONSTRAINTS = {
    1: [
        "A viral traffic spike just hit. Scale this to handle 100x concurrent requests "
        "using a distributed rate limiter (Redis-backed).",
        "The upstream API now has a 100ms SLA. Add request caching with a 60-second TTL.",
    ],
    2: [
        "Your rate limiter backend (Redis) just lost quorum. Implement a fallback "
        "using in-memory LRU cache with TTL.",
        "Add a circuit breaker around the proxy so a failing upstream doesn't cascade.",
        "Log every rate-limited request to a dead-letter topic for audit analysis.",
    ],
    3: [
        "A security audit flagged the proxy. Add request signature validation using "
        "HMAC-SHA256 for all incoming requests.",
        "The service must now run across 3 regions. Make the rate limiter region-aware "
        "with eventual consistency.",
        "Implement graceful shutdown — drain in-flight requests before stopping.",
    ],
}


def escalate_challenge(state: DevAscentState) -> dict:
    """Apply escalation constraints to the current challenge.

    In production this calls an LLM with the escalation prompt template
    to generate creative, context-aware constraints. For now, uses
    a predefined constraint catalog.
    """
    depth = state.get("escalation_depth", 0) + 1
    depth = min(depth, 3)

    constraints = ESCALATION_CONSTRAINTS.get(depth, [])
    existing = list(state.get("escalation_constraints", []))
    existing.extend(constraints)

    return {
        "escalation_depth": depth,
        "escalation_constraints": existing,
    }
