"""DevAscent Skill Coach.

Turns one-shot assessment scores into a persistent, growing personal
curriculum. Bridges the assessment FSM into a durable learning journal,
a spaced-repetition practice schedule, and (optionally) hermes
cross-session memory so the agent can coach the user over time.

The previous design left the assessment engine siloed: evaluations wrote
only to the LangGraph Postgres checkpoint and never fed back into a
skill-building loop. This package closes that gap.
"""
from devascent.coach.journal import JournalEntry, LearningJournal
from devascent.coach.curriculum import (
    SkillStat,
    PracticeItem,
    build_curriculum,
    skill_stats,
)
from devascent.coach.coach import CoachReport, build_coach_report

__all__ = [
    "JournalEntry",
    "LearningJournal",
    "SkillStat",
    "PracticeItem",
    "build_curriculum",
    "skill_stats",
    "CoachReport",
    "build_coach_report",
]
