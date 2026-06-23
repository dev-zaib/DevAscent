"""PresentChallenge node — RAG-driven challenge selection."""
from datetime import datetime, timezone
from devascent.assessment.state import DevAscentState
from devascent.rag.retriever import retriever
from devascent.rag.seed_data import SEED_CHALLENGES


async def present_challenge(state: DevAscentState) -> dict:
    """Select and present the next challenge based on user's skills matrix.

    Uses RAG retriever: embeds user's weakest skills, searches pgvector
    for matching challenges, deduplicates against attempted challenges.

    Falls back to the first un-attempted challenge if no vector match.
    """
    skills_matrix = state.get("skills_matrix", {})
    history = state.get("evaluation_history", [])

    attempted_ids = [entry.get("challenge_id", "") for entry in history]
    current_level = state.get("current_level", "BASELINE")

    # Try RAG retrieval
    challenge = await retriever.retrieve(
        skills_matrix=skills_matrix,
        attempted_ids=attempted_ids,
    )

    # Fallback: first challenge matching current level, not attempted
    if not challenge:
        for chal in SEED_CHALLENGES:
            if chal["title"] in attempted_ids:
                continue
            if chal.get("target_level") == current_level:
                challenge = chal
                break

    # Ultimate fallback
    if not challenge:
        challenge = SEED_CHALLENGES[0]

    challenge_id = challenge["title"]

    state_update = {
        "active_challenge_id": challenge_id,
        "active_challenge_data": challenge,
        "challenge_attempt": state.get("challenge_attempt", 0) + 1,
        "last_evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return state_update
