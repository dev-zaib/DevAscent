"""DetermineNextStep node — decides next action based on evaluation score."""
from devascent.assessment.state import DevAscentState

LEVEL_ORDER = ["BASELINE", "SYSTEM_DESIGNER", "TOP_1_PERCENT", "ARCHITECT", "DISTINGUISHED"]


def determine_next_step(state: DevAscentState) -> dict:
    """Determine the next action after evaluation.

    Routing logic:
      score >= 85 AND level == BASELINE AND depth < 3 → escalate
      score >= 85 AND (level != BASELINE OR depth >= 3) → advance level
      score >= 70 → keep level, present variant challenge
      score >= 40 → reinforce weak dimension
      score < 40  → flag for human review
    """
    score = state.get("latest_score", 0.0)
    level = state.get("current_level", "BASELINE")
    depth = state.get("escalation_depth", 0)

    if score >= 85:
        if level == "BASELINE" and depth < 3:
            return {"next_action": "escalate"}
        else:
            return advance_level(state)

    if score >= 70:
        return {
            "next_action": "keep_level",
        }

    if score >= 40:
        return {
            "next_action": "reinforce",
        }

    return {"next_action": "flag_review"}


def advance_level(state: DevAscentState) -> dict:
    """Advance the user to the next engineering level."""
    current = state.get("current_level", "BASELINE")
    try:
        idx = LEVEL_ORDER.index(current)
        next_level = LEVEL_ORDER[min(idx + 1, len(LEVEL_ORDER) - 1)]
    except ValueError:
        next_level = "BASELINE"

    return {
        "next_action": "advance_level",
        "current_level": next_level,
        "escalation_depth": 0,
    }
