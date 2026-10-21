"""Coach API routes — personal progress + curriculum.

Reads the durable learning journal directly, so these endpoints work even
when LangGraph/Postgres are offline. This is the surface the UI uses to
render the progress dashboard and the "what to practice next" panel.
"""
from fastapi import APIRouter

from devascent.coach.journal import LearningJournal
from devascent.coach.coach import build_coach_report
from devascent.coach.curriculum import build_curriculum, skill_stats

router = APIRouter(tags=["coach"])


@router.get("/progress/{user_id}")
def get_progress(user_id: str) -> dict:
    """Full coach report: mastery, momentum, strongest/weakest, milestones."""
    journal = LearningJournal(user_id)
    entries = journal.read_all()
    matrix = {s.skill: s.current for s in skill_stats(entries).values()}
    report = build_coach_report(user_id, entries, matrix)
    return report.to_dict()


@router.get("/curriculum/{user_id}")
def get_curriculum(user_id: str, limit: int = 5) -> dict:
    """Ranked next-practice recommendations (weakness + spaced repetition)."""
    journal = LearningJournal(user_id)
    entries = journal.read_all()
    matrix = {s.skill: s.current for s in skill_stats(entries).values()}
    items = build_curriculum(entries, matrix, limit=limit)
    return {
        "user_id": user_id,
        "count": len(items),
        "items": [
            {
                "skill": i.skill,
                "current": i.current,
                "band": i.band,
                "priority": i.priority,
                "due": i.due,
                "overdue_days": i.overdue_days,
                "reason": i.reason,
                "recommended_action": i.recommended_action,
                "target_score": i.target_score,
            }
            for i in items
        ],
    }


@router.get("/history/{user_id}")
def get_history(user_id: str, limit: int = 50) -> dict:
    """Recent evaluation journal entries (most recent last)."""
    journal = LearningJournal(user_id)
    entries = journal.recent(limit)
    return {
        "user_id": user_id,
        "count": len(entries),
        "entries": [e.to_dict() for e in entries],
    }
