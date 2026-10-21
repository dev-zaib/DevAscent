"""Curriculum + spaced-repetition engine.

Pure functions over a list of journal entries. No I/O, no clock except an
injectable ``now`` — so the whole thing is deterministic and unit-testable.

Two jobs:
  1. ``skill_stats`` — aggregate per-skill mastery, trend, and recency from
     the learning journal.
  2. ``build_curriculum`` — rank what to practice next, blending weakness,
     downward trend, and spaced-repetition due-dates (SM-2 inspired).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from devascent.coach.journal import JournalEntry

# Mastery bands (0-100).
FRAGILE = 40.0
DEVELOPING = 70.0
PROFICIENT = 85.0

# Spaced-repetition intervals in days, indexed by consecutive strong reps.
SR_INTERVALS = [1, 2, 4, 7, 14, 30, 60]
STRONG_SCORE = DEVELOPING  # a rep counts as "strong" at >= 70


def _band(score: float) -> str:
    if score < FRAGILE:
        return "fragile"
    if score < DEVELOPING:
        return "developing"
    if score < PROFICIENT:
        return "proficient"
    return "strong"


def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


@dataclass
class SkillStat:
    skill: str
    current: float
    attempts: int
    trend: float  # slope of recent scores: + improving, - regressing
    last_score: float
    band: str
    consecutive_strong: int
    last_practiced: str | None
    history: list[float] = field(default_factory=list)


@dataclass
class PracticeItem:
    skill: str
    current: float
    band: str
    priority: float          # higher = practice sooner
    due: bool                # spaced-repetition window elapsed
    overdue_days: float
    reason: str
    recommended_action: str
    target_score: float


def _linear_trend(scores: list[float]) -> float:
    """Least-squares slope over the (index, score) points. 0 if < 2 points."""
    n = len(scores)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(scores) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, scores))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return round(num / den, 3)


def skill_stats(entries: list[JournalEntry]) -> dict[str, SkillStat]:
    """Aggregate per-skill stats from the journal in chronological order."""
    series: dict[str, list[tuple[str, float]]] = {}
    for e in entries:
        for skill, score in (e.rubric_scores or {}).items():
            series.setdefault(skill, []).append((e.timestamp, float(score)))

    stats: dict[str, SkillStat] = {}
    for skill, points in series.items():
        scores = [s for _, s in points]
        recent = scores[-5:]
        # Count strong reps from the end (consecutive).
        consec = 0
        for s in reversed(scores):
            if s >= STRONG_SCORE:
                consec += 1
            else:
                break
        stats[skill] = SkillStat(
            skill=skill,
            current=round(scores[-1], 2),
            attempts=len(scores),
            trend=_linear_trend(recent),
            last_score=round(scores[-1], 2),
            band=_band(scores[-1]),
            consecutive_strong=consec,
            last_practiced=points[-1][0],
            history=scores,
        )
    return stats


def _due_state(stat: SkillStat, now: datetime) -> tuple[bool, float]:
    """Spaced-repetition due check. Returns (due, overdue_days)."""
    last = _parse_ts(stat.last_practiced or "")
    if last is None:
        return True, 0.0
    idx = min(stat.consecutive_strong, len(SR_INTERVALS) - 1)
    interval = SR_INTERVALS[idx]
    # Weak skills get tighter intervals regardless of streak.
    if stat.current < FRAGILE:
        interval = min(interval, 1)
    elif stat.current < DEVELOPING:
        interval = min(interval, 3)
    next_due = last + timedelta(days=interval)
    overdue = (now - next_due).total_seconds() / 86400.0
    return overdue >= 0, round(overdue, 2)


def _action_for(stat: SkillStat) -> tuple[str, float]:
    """Human recommendation + target score for the next rep."""
    if stat.band == "fragile":
        return (
            f"Drill fundamentals of '{stat.skill}'. Take a focused variant "
            f"and slow down — accuracy over speed.",
            FRAGILE,
        )
    if stat.band == "developing":
        return (
            f"Reinforce '{stat.skill}' with a fresh scenario; aim to apply it "
            f"without hints.",
            DEVELOPING,
        )
    if stat.band == "proficient":
        return (
            f"Push '{stat.skill}' under added constraints (scale, latency, "
            f"failure modes) to reach mastery.",
            PROFICIENT,
        )
    return (
        f"Maintain '{stat.skill}' — spaced refresh only; spend effort "
        f"elsewhere.",
        100.0,
    )


def build_curriculum(
    entries: list[JournalEntry],
    skills_matrix: dict[str, float] | None = None,
    now: datetime | None = None,
    limit: int = 5,
) -> list[PracticeItem]:
    """Rank what to practice next.

    Priority blends: weakness (lower score → higher), downward trend, and
    spaced-repetition due/overdue. ``skills_matrix`` (the live FSM matrix)
    seeds skills that have no journal history yet.
    """
    now = now or datetime.now(timezone.utc)
    stats = skill_stats(entries)

    # Seed unseen skills from the live matrix so brand-new dimensions surface.
    for skill, score in (skills_matrix or {}).items():
        if skill not in stats:
            stats[skill] = SkillStat(
                skill=skill,
                current=round(float(score), 2),
                attempts=0,
                trend=0.0,
                last_score=round(float(score), 2),
                band=_band(float(score)),
                consecutive_strong=0,
                last_practiced=None,
                history=[float(score)],
            )

    items: list[PracticeItem] = []
    for stat in stats.values():
        due, overdue_days = _due_state(stat, now)
        # Weakness contributes most; cap at 100.
        weakness = max(0.0, 100.0 - stat.current)
        priority = weakness
        reasons: list[str] = [f"{stat.band} ({stat.current:.0f}/100)"]
        if stat.trend < -1.0:
            priority += 20.0
            reasons.append(f"regressing (trend {stat.trend:+.1f})")
        elif stat.trend > 1.0:
            reasons.append(f"improving (trend {stat.trend:+.1f})")
        if due:
            priority += 15.0 + min(overdue_days, 30.0)
            reasons.append(
                "due for review" if overdue_days < 1 else f"{overdue_days:.0f}d overdue"
            )
        if stat.attempts == 0:
            priority += 10.0
            reasons.append("not yet assessed")

        action, target = _action_for(stat)
        items.append(
            PracticeItem(
                skill=stat.skill,
                current=stat.current,
                band=stat.band,
                priority=round(priority, 2),
                due=due,
                overdue_days=overdue_days,
                reason=", ".join(reasons),
                recommended_action=action,
                target_score=target,
            )
        )

    items.sort(key=lambda i: i.priority, reverse=True)
    return items[:limit]
