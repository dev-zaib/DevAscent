"""CoachProgress node — un-silos the assessment engine.

Runs after UpdateSkillsMatrix. Records the evaluation into the durable
learning journal, rebuilds the personal curriculum + coach report, and
bridges a progress note into hermes cross-session memory. The report and
curriculum are returned into graph state so the API/UI can surface them.

Best-effort: a coaching/persistence failure must never break the
assessment run, so the whole body is guarded.
"""
from __future__ import annotations

from devascent.assessment.state import DevAscentState


def coach_progress(state: DevAscentState) -> dict:
    try:
        from devascent.coach.journal import JournalEntry, LearningJournal
        from devascent.coach.coach import build_coach_report
        from devascent.coach.memory_bridge import write_progress_memory

        user_id = state.get("user_id") or "anonymous"
        journal = LearningJournal(user_id)

        entry = JournalEntry(
            challenge_id=state.get("active_challenge_id", ""),
            level=state.get("current_level", "BASELINE"),
            score=float(state.get("latest_score", 0.0)),
            rubric_scores=dict(state.get("rubric_scores", {})),
            skill_deltas=dict(state.get("skill_deltas", {})),
            ai_feedback=state.get("ai_feedback", ""),
            constraints_applied=list(state.get("escalation_constraints", [])),
            escalation_depth=int(state.get("escalation_depth", 0)),
            timestamp=state.get("last_evaluation_timestamp", ""),
        )
        journal.append(entry)

        report = build_coach_report(
            user_id=user_id,
            entries=journal.read_all(),
            skills_matrix=dict(state.get("skills_matrix", {})),
            level=state.get("current_level", "BASELINE"),
        )
        write_progress_memory(report)

        return {
            "coach_report": report.to_dict(),
            "curriculum": [item.skill for item in report.curriculum],
        }
    except Exception as exc:  # noqa: BLE001 — coaching is non-critical
        return {"coach_error": str(exc)}
