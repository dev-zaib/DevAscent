"""UpdateSkillsMatrix node — weighted recalculation of skill scores."""
from devascent.assessment.state import DevAscentState


DECAY_FACTOR = 0.7  # Old score weight
NEW_WEIGHT = 0.3  # New evaluation weight


def update_skills_matrix(state: DevAscentState) -> dict:
    """Update the skills matrix based on latest evaluation.

    Formula: new_score = old_score * DECAY_FACTOR + eval_score * NEW_WEIGHT
    Skills not present in this evaluation are preserved as-is.
    """
    skills = dict(state.get("skills_matrix", {}))
    rubric_scores = state.get("rubric_scores", {})

    for skill, score in rubric_scores.items():
        old = skills.get(skill, 0.0)
        skills[skill] = round(old * DECAY_FACTOR + score * NEW_WEIGHT, 2)

    return {"skills_matrix": skills}
