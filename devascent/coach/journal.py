"""Durable per-user learning journal.

Append-only JSONL, one entry per evaluation. This is the source of truth
for skill growth over time — independent of the LangGraph Postgres
checkpoint (which only holds the *current* run state). The journal is what
makes progress legible across sessions and powers the curriculum engine.

Pure I/O with an injectable root path so it is fully testable without any
database, Redis, or running agent.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def _default_root() -> Path:
    """Coach data root, under the devascent home (defaults to ~/.hermes)."""
    try:
        from devascent_constants import get_devascent_home

        return Path(get_devascent_home()) / "coach"
    except Exception:
        # Fallback keeps the module importable in minimal environments.
        return Path(os.environ.get("DEVASCENT_COACH_HOME", ".devascent-coach"))


@dataclass
class JournalEntry:
    """One recorded evaluation outcome."""

    challenge_id: str
    level: str
    score: float
    rubric_scores: dict[str, float] = field(default_factory=dict)
    skill_deltas: dict[str, float] = field(default_factory=dict)
    ai_feedback: str = ""
    constraints_applied: list[str] = field(default_factory=list)
    escalation_depth: int = 0
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "JournalEntry":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


class LearningJournal:
    """Append-only JSONL journal for a single user."""

    def __init__(self, user_id: str, root: Path | str | None = None) -> None:
        if not user_id:
            raise ValueError("user_id is required")
        self.user_id = user_id
        self.root = Path(root) if root is not None else _default_root()
        # Sanitize to a safe filename component.
        safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in user_id)
        self.path = self.root / f"{safe}.jsonl"

    def append(self, entry: JournalEntry) -> JournalEntry:
        """Append one entry durably (create parent dirs as needed)."""
        self.root.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry.to_dict(), ensure_ascii=False)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return entry

    def read_all(self) -> list[JournalEntry]:
        """Read every entry in chronological (append) order."""
        if not self.path.exists():
            return []
        out: list[JournalEntry] = []
        with open(self.path, "r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    out.append(JournalEntry.from_dict(json.loads(raw)))
                except (json.JSONDecodeError, TypeError):
                    # A corrupt line should not sink the whole history.
                    continue
        return out

    def recent(self, n: int = 10) -> list[JournalEntry]:
        return self.read_all()[-n:]

    def count(self) -> int:
        return len(self.read_all())

    def rewrite(self, entries: Iterable[JournalEntry]) -> None:
        """Atomically replace the journal (used for compaction/repair)."""
        self.root.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.root, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                for e in entries:
                    fh.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
