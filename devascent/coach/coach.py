"""Coach report — the human-facing synthesis layer.

Pulls the journal + curriculum together into a single legible picture:
where you are, where you're slipping, and exactly what to practice next.
Pure (injectable ``now``); no I/O here — persistence lives in
``memory_bridge``.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from devascent.coach.journal import JournalEntry
from devascent.coach.curriculum import (
    PracticeItem,
    SkillStat,
    build_curriculum,
    skill_stats,
)


@dataclass
class CoachReport:
    user_id: str
    generated_at: str
    level: str
    total_evaluations: int
    overall_mastery: float           # mean of current skill scores
    momentum: float                  # mean recent trend across skills
    strongest: list[tuple[str, float]]
    weakest: list[tuple[str, float]]
    curriculum: list[PracticeItem]
    summary: str
    milestones: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["curriculum"] = [asdict(p) for p in self.curriculum]
        return d


def _milestones(stats: dict[str, SkillStat], total: int) -> list[str]:
    out: list[str] = []
    mastered = [s.skill for s in stats.values() if s.band == "strong"]
    if mastered:
        out.append(f"Mastered: {', '.join(sorted(mastered))}")
    rising = [s.skill for s in stats.values() if s.trend > 2.0]
    if rising:
        out.append(f"Fastest gains: {', '.join(sorted(rising))}")
    if total >= 10:
        out.append(f"{total} evaluations logged — consistent practice")
    return out


def build_coach_report(
    user_id: str,
    entries: list[JournalEntry],
    skills_matrix: dict[str, float] | None = None,
    level: str = "BASELINE",
    now: datetime | None = None,
) -> CoachReport:
    now = now or datetime.now(timezone.utc)
    stats = skill_stats(entries)

    # Merge live matrix for skills with no journal history.
    merged: dict[str, float] = {s.skill: s.current for s in stats.values()}
    for skill, score in (skills_matrix or {}).items():
        merged.setdefault(skill, round(float(score), 2))

    if merged:
        overall = round(sum(merged.values()) / len(merged), 2)
        ranked = sorted(merged.items(), key=lambda kv: kv[1], reverse=True)
        strongest = ranked[:3]
        weakest = sorted(merged.items(), key=lambda kv: kv[1])[:3]
    else:
        overall, strongest, weakest = 0.0, [], []

    trends = [s.trend for s in stats.values()]
    momentum = round(sum(trends) / len(trends), 2) if trends else 0.0

    curriculum = build_curriculum(entries, skills_matrix, now=now, limit=5)

    # Summary line — short, actionable.
    if not entries and not skills_matrix:
        summary = "No assessments yet. Start a baseline challenge to calibrate your skill matrix."
    else:
        focus = curriculum[0].skill if curriculum else "—"
        direction = (
            "trending up" if momentum > 0.5
            else "trending down" if momentum < -0.5
            else "holding steady"
        )
        summary = (
            f"Level {level}; overall mastery {overall:.0f}/100, {direction}. "
            f"Next focus: {focus}."
        )

    return CoachReport(
        user_id=user_id,
        generated_at=now.isoformat(),
        level=level,
        total_evaluations=len(entries),
        overall_mastery=overall,
        momentum=momentum,
        strongest=strongest,
        weakest=weakest,
        curriculum=curriculum,
        summary=summary,
        milestones=_milestones(stats, len(entries)),
    )
