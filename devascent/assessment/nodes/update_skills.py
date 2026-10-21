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

    deltas: dict[str, float] = {}
    for skill, score in rubric_scores.items():
        old = skills.get(skill, 0.0)
        if skill in skills:
            new = round(old * DECAY_FACTOR + score * NEW_WEIGHT, 2)
        else:
            new = round(float(score), 2)  # first observation seeds at full value
        skills[skill] = new
        deltas[skill] = round(new - old, 2)

    # skill_deltas feed the coach node's journal entry (growth over time).
    return {"skills_matrix": skills, "skill_deltas": deltas}
