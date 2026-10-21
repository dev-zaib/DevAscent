"""Bridge assessment progress into hermes cross-session memory.

This is the piece that un-silos the assessment engine: after each
evaluation the coach writes a compact, human-readable progress note where
the hermes agent's memory layer can pick it up, plus a machine-readable
snapshot for tooling. The agent can then coach the user with full
awareness of their skill history — across sessions, not just within one
LangGraph run.

Best-effort and dependency-light: if the hermes memory directory or
constants are unavailable we degrade gracefully and still write the
snapshot under the coach root.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from devascent.coach.coach import CoachReport


def _memory_root() -> Path:
    try:
        from devascent_constants import get_devascent_home

        return Path(get_devascent_home()) / "memory" / "devascent"
    except Exception:
        return Path(os.environ.get("DEVASCENT_COACH_HOME", ".devascent-coach")) / "memory"


def _render_markdown(report: CoachReport) -> str:
    lines = [
        f"# DevAscent skill progress — {report.user_id}",
        "",
        f"_Updated {report.generated_at} · level {report.level} · "
        f"{report.total_evaluations} evaluations_",
        "",
        f"**Summary:** {report.summary}",
        "",
        f"**Overall mastery:** {report.overall_mastery:.0f}/100  ·  "
        f"**Momentum:** {report.momentum:+.1f}",
        "",
    ]
    if report.strongest:
        lines.append(
            "**Strongest:** "
            + ", ".join(f"{k} ({v:.0f})" for k, v in report.strongest)
        )
    if report.weakest:
        lines.append(
            "**Weakest:** "
            + ", ".join(f"{k} ({v:.0f})" for k, v in report.weakest)
        )
    if report.curriculum:
        lines += ["", "**Recommended practice (next):**"]
        for i, item in enumerate(report.curriculum, 1):
            lines.append(
                f"{i}. `{item.skill}` — {item.recommended_action} "
                f"({item.reason})"
            )
    if report.milestones:
        lines += ["", "**Milestones:** " + "; ".join(report.milestones)]
    lines.append("")
    return "\n".join(lines)


def write_progress_memory(
    report: CoachReport, root: Path | str | None = None
) -> dict[str, str]:
    """Persist the report as a markdown memory note + JSON snapshot.

    Returns the paths written. Safe to call on every evaluation; the
    markdown note for a user is overwritten (latest wins) while the JSON
    snapshot mirrors it for programmatic access.
    """
    base = Path(root) if root is not None else _memory_root()
    base.mkdir(parents=True, exist_ok=True)

    safe = "".join(
        c if c.isalnum() or c in ("-", "_") else "_" for c in report.user_id
    )
    md_path = base / f"progress-{safe}.md"
    json_path = base / f"progress-{safe}.json"

    _atomic_write(md_path, _render_markdown(report))
    _atomic_write(json_path, json.dumps(report.to_dict(), ensure_ascii=False, indent=2))

    return {"markdown": str(md_path), "json": str(json_path)}


def _atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
