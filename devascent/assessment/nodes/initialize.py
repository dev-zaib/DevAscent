"""InitializeAssessment node — boots state from PostgreSQL, seeds initial matrix."""
import uuid
from devascent.assessment.state import DevAscentState, make_initial_state


def initialize_assessment(state: DevAscentState) -> dict:
    """Initialize a new assessment session.

    In production this queries the database for an existing session
    or creates a new one. For now, it initializes from the provided
    user_id or creates default state.
    """
    if state.get("user_id") and state.get("session_start_time"):
        return {}

    user_id = state.get("user_id", str(uuid.uuid4()))
    initial = make_initial_state(user_id)
    initial["active_challenge_id"] = ""
    return initial
