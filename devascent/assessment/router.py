"""Conditional routing — maps next_action to graph node."""
from devascent.assessment.state import DevAscentState


def route_after_determine(state: DevAscentState) -> str:
    """Map the next_action decision to the next graph node.

    Returns:
        "escalate" — trigger Go Harder escalation loop
        "present_challenge" — present next challenge (keep level, reinforce, advance)
        "__end__" — end the session (flag_review)
    """
    action = state.get("next_action", "")

    if action == "escalate":
        return "escalate"

    if action == "flag_review":
        return "__end__"

    # keep_level, reinforce, advance_level — all go to present_challenge
    return "present_challenge"
