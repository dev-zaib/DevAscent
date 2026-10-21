"""Unit tests for the DevAscent Skill Coach layer.

Pure + infra-free: no Postgres, Redis, langgraph, or running agent. Runs
under pytest *and* standalone (`python tests/devascent/test_coach.py`) so
it works even where pytest is not installed in the venv.
"""
from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from devascent.coach.journal import JournalEntry, LearningJournal
from devascent.coach.curriculum import (
    build_curriculum,
    skill_stats,
    SR_INTERVALS,
)
from devascent.coach.coach import build_coach_report
from devascent.coach.memory_bridge import write_progress_memory


def _entry(skill_scores, ts, score=None, challenge="c1", level="BASELINE"):
    return JournalEntry(
        challenge_id=challenge,
        level=level,
        score=score if score is not None else max(skill_scores.values()),
        rubric_scores=skill_scores,
        timestamp=ts,
    )


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# --------------------------------------------------------------------------- #
# Journal
# --------------------------------------------------------------------------- #
def test_journal_append_and_read_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        j = LearningJournal("user-1", root=d)
        assert j.read_all() == []
        j.append(_entry({"async_flows": 50.0}, _iso(datetime(2026, 1, 1, tzinfo=timezone.utc))))
        j.append(_entry({"async_flows": 70.0}, _iso(datetime(2026, 1, 2, tzinfo=timezone.utc))))
        entries = j.read_all()
        assert len(entries) == 2
        assert entries[0].rubric_scores["async_flows"] == 50.0
        assert entries[1].rubric_scores["async_flows"] == 70.0
        assert j.count() == 2
        assert len(j.recent(1)) == 1


def test_journal_skips_corrupt_lines():
    with tempfile.TemporaryDirectory() as d:
        j = LearningJournal("u", root=d)
        j.append(_entry({"x": 10.0}, _iso(datetime(2026, 1, 1, tzinfo=timezone.utc))))
        with open(j.path, "a", encoding="utf-8") as fh:
            fh.write("{not valid json\n")
        assert len(j.read_all()) == 1  # corrupt line ignored, valid survives


def test_journal_user_id_sanitized():
    with tempfile.TemporaryDirectory() as d:
        j = LearningJournal("a/b c", root=d)
        assert "/" not in j.path.name
        j.append(_entry({"x": 1.0}, _iso(datetime(2026, 1, 1, tzinfo=timezone.utc))))
        assert j.path.exists()


# --------------------------------------------------------------------------- #
# Curriculum / stats
# --------------------------------------------------------------------------- #
def test_skill_stats_trend_and_band():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    entries = [
        _entry({"caching": 40.0}, _iso(base)),
        _entry({"caching": 60.0}, _iso(base + timedelta(days=1))),
        _entry({"caching": 80.0}, _iso(base + timedelta(days=2))),
    ]
    stats = skill_stats(entries)
    s = stats["caching"]
    assert s.current == 80.0
    assert s.band == "proficient"
    assert s.trend > 0          # improving
    assert s.attempts == 3
    assert s.consecutive_strong == 1  # only 80 >= 70 (60 is below)


def test_curriculum_prioritizes_weakest():
    base = datetime(2026, 6, 1, tzinfo=timezone.utc)
    entries = [
        _entry({"strong_skill": 90.0}, _iso(base)),
        _entry({"weak_skill": 20.0}, _iso(base)),
    ]
    items = build_curriculum(entries, now=base + timedelta(days=2))
    assert items[0].skill == "weak_skill"
    assert items[0].band == "fragile"
    # weakest must outrank the strong one
    skills_ranked = [i.skill for i in items]
    assert skills_ranked.index("weak_skill") < skills_ranked.index("strong_skill")


def test_curriculum_seeds_unassessed_skills_from_matrix():
    items = build_curriculum([], skills_matrix={"new_dim": 0.0}, now=datetime(2026, 6, 1, tzinfo=timezone.utc))
    assert any(i.skill == "new_dim" for i in items)
    item = next(i for i in items if i.skill == "new_dim")
    assert "not yet assessed" in item.reason


def test_spaced_repetition_not_due_when_recent_and_strong():
    base = datetime(2026, 6, 1, tzinfo=timezone.utc)
    # Many strong reps → long interval; last rep just now → not due.
    entries = [
        _entry({"sched": 95.0}, _iso(base + timedelta(days=i)))
        for i in range(len(SR_INTERVALS) + 2)
    ]
    last = base + timedelta(days=len(SR_INTERVALS) + 1)
    items = build_curriculum(entries, now=last)  # evaluate "today"
    sched = next((i for i in items if i.skill == "sched"), None)
    # Strong + just practiced → either filtered out of top-5 or not due.
    if sched is not None:
        assert sched.due is False


def test_spaced_repetition_due_when_overdue():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    entries = [_entry({"rusty": 95.0}, _iso(base))]
    # 100 days later, far past any interval → due/overdue.
    items = build_curriculum(entries, now=base + timedelta(days=100))
    rusty = next(i for i in items if i.skill == "rusty")
    assert rusty.due is True
    assert rusty.overdue_days > 0


# --------------------------------------------------------------------------- #
# Coach report
# --------------------------------------------------------------------------- #
def test_coach_report_empty_state():
    r = build_coach_report("u", [], {})
    assert r.total_evaluations == 0
    assert "No assessments yet" in r.summary


def test_coach_report_strong_weak_and_momentum():
    base = datetime(2026, 6, 1, tzinfo=timezone.utc)
    entries = [
        _entry({"a": 30.0, "b": 90.0}, _iso(base)),
        _entry({"a": 35.0, "b": 92.0}, _iso(base + timedelta(days=1))),
    ]
    r = build_coach_report("u", entries, {}, level="BASELINE", now=base + timedelta(days=2))
    assert r.weakest[0][0] == "a"
    assert r.strongest[0][0] == "b"
    assert r.total_evaluations == 2
    assert isinstance(r.overall_mastery, float)


# --------------------------------------------------------------------------- #
# Memory bridge
# --------------------------------------------------------------------------- #
def test_memory_bridge_writes_markdown_and_json():
    with tempfile.TemporaryDirectory() as d:
        r = build_coach_report("user-xyz", [], {"caching": 80.0, "async_flows": 30.0})
        paths = write_progress_memory(r, root=d)
        md = Path(paths["markdown"])
        js = Path(paths["json"])
        assert md.exists() and js.exists()
        text = md.read_text(encoding="utf-8")
        assert "DevAscent skill progress" in text
        assert "user-xyz" in text


# --------------------------------------------------------------------------- #
# Standalone runner (no pytest required)
# --------------------------------------------------------------------------- #
def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} coach tests passed")


if __name__ == "__main__":
    _run_all()
