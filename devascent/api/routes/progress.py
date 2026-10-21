"""Progress API — mark topics complete and read what's been learned.

The user explicitly marks a topic done; the coach/assessment then analyzes
and quizzes ONLY those completed topics.

POST /api/progress/complete {user_id, skill, label, done}
GET  /api/progress/{user_id} -> {completed: {skill: {label, ts}}}
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["progress"])


class CompleteRequest(BaseModel):
    user_id: str
    skill: str
    label: str = ""
    done: bool = True


def _path(user_id: str) -> Path:
    try:
        from devascent_constants import get_devascent_home
        base = Path(get_devascent_home()) / "coach"
    except Exception:
        base = Path(".devascent-coach")
    base.mkdir(parents=True, exist_ok=True)
    su = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in user_id)
    return base / f"completed-{su}.json"


def _read(user_id: str) -> dict:
    p = _path(user_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


@router.post("/complete")
def complete(body: CompleteRequest) -> dict:
    data = _read(body.user_id)
    if body.done:
        data[body.skill] = {"label": body.label or body.skill,
                            "ts": datetime.now(timezone.utc).isoformat()}
    else:
        data.pop(body.skill, None)
    try:
        _path(body.user_id).write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass
    return {"completed": data, "count": len(data)}


@router.get("/{user_id}")
def get_progress(user_id: str) -> dict:
    data = _read(user_id)
    return {"completed": data, "count": len(data)}
