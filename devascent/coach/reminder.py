"""Daily practice reminder — the skill-building habit loop.

Standalone and infra-free: reads the durable journal and prints the
practice items that are *due* (spaced-repetition window elapsed) or weak.
Designed to be invoked by the surviving hermes cron system on a daily
schedule so the agent nudges the user toward their weakest skills — the
piece that turns one-off assessments into deliberate, compounding practice.

Usage:
    python -m devascent.coach.reminder <user_id> [--limit N] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys

from devascent.coach.journal import LearningJournal
from devascent.coach.curriculum import build_curriculum, skill_stats


def due_practice(user_id: str, limit: int = 5) -> list[dict]:
    """Return due/weak practice items as plain dicts (cron/JSON friendly)."""
    journal = LearningJournal(user_id)
    entries = journal.read_all()
    matrix = {s.skill: s.current for s in skill_stats(entries).values()}
    items = build_curriculum(entries, matrix, limit=limit)
    # Surface due items first; if nothing is due, still show the weakest.
    due = [i for i in items if i.due] or items
    return [
        {
            "skill": i.skill,
            "current": i.current,
            "band": i.band,
            "due": i.due,
            "overdue_days": i.overdue_days,
            "action": i.recommended_action,
            "reason": i.reason,
        }
        for i in due
    ]


def render_text(user_id: str, items: list[dict]) -> str:
    if not items:
        return f"DevAscent · {user_id}: no practice history yet — run a baseline challenge."
    lines = [f"DevAscent · daily practice for {user_id}:"]
    for n, it in enumerate(items, 1):
        tag = "DUE" if it["due"] else "focus"
        lines.append(
            f"  {n}. [{tag}] {it['skill']} ({it['current']:.0f}/100, {it['band']}) — {it['action']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DevAscent daily practice reminder")
    ap.add_argument("user_id")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args(argv)

    items = due_practice(args.user_id, args.limit)
    if args.json:
        print(json.dumps({"user_id": args.user_id, "items": items}, ensure_ascii=False))
    else:
        print(render_text(args.user_id, items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
