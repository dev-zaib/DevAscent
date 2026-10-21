"""Learn API — interactive, narratable lesson for a roadmap node.

POST /api/learn/lesson {node, skill?, language?, user_id?, regenerate?}
  -> lesson (narration script, key points, Mermaid visual, playable widget).

Lessons are cached per (user, node) so re-opening returns the SAME content
instantly (no surprise regeneration). `regenerate: true` forces a fresh
DeepSeek generation and overwrites the cache. Offline mock keeps it usable
without a key.
"""
import json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["learn"])


class LessonRequest(BaseModel):
    node: str
    skill: str = ""
    language: str = "javascript"
    user_id: str | None = None
    regenerate: bool = False


def _lesson_path(user_id: str, key: str) -> Path:
    try:
        from devascent_constants import get_devascent_home
        base = Path(get_devascent_home()) / "coach"
    except Exception:
        base = Path(".devascent-coach")
    base.mkdir(parents=True, exist_ok=True)
    su = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in user_id)
    sk = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in key)[:60]
    return base / f"lesson-{su}-{sk}.json"


def _mock_lesson(node: str, skill: str, language: str) -> dict:
    return {
        "concept": (
            f"{node} is a core building block. Learn the smallest correct version first, "
            "then layer on the production concerns."
        ),
        "narration_script": (
            f"Let's learn {node}. Start simple. First, understand the core idea in one sentence. "
            "Then build the simplest version that works for one case. Once that's solid, you add "
            "the harder parts: edge cases, failures, and scale. Take it one step at a time, and "
            "test as you go. You've got this."
        ),
        "key_points": [
            f"What {node} is and why it matters",
            "The simplest correct implementation",
            "Common edge cases",
            "Production concerns (failure, scale)",
        ],
        "approach_steps": [
            "Restate the idea in your own words.",
            "Build the happy path.",
            "Add edge cases.",
            "Add production hardening.",
        ],
        "visual_kind": "mermaid",
        "visual_spec": (
            "graph TD\n"
            f"  A[\"{node}\"] --> B[\"Core idea\"]\n"
            "  B --> C[\"Happy path\"]\n"
            "  C --> D[\"Edge cases\"]\n"
            "  D --> E[\"Production-ready\"]"
        ),
        "widget_html": (
            "<h3>Explore</h3><p>Drag the slider to see the idea scale.</p>"
            "<div style='height:12px;border-radius:99px;background:#EDEAE1;overflow:hidden;margin:14px 0'>"
            "<i id='f' style='display:block;height:100%;width:30%;background:#C96442'></i></div>"
            "<input id='s' type='range' min='0' max='100' value='30' style='width:80%'>"
            "<div>load: <code id='v'>30</code>%</div>"
            "<script>const s=document.getElementById('s'),f=document.getElementById('f'),v=document.getElementById('v');"
            "s.oninput=()=>{f.style.width=s.value+'%';v.textContent=s.value;};</script>"
        ),
        "study_terms": [skill or node, "best practices", "edge cases"],
        "provider": "mock",
    }


def _generate(node: str, skill: str, language: str) -> dict:
    try:
        from devascent.llm import deepseek
        if deepseek.is_configured():
            return deepseek.generate_lesson(node, skill, language)
    except Exception:
        pass
    return _mock_lesson(node, skill, language)


@router.post("/lesson")
def lesson(body: LessonRequest) -> dict:
    key = body.skill or body.node
    path = body.user_id and _lesson_path(body.user_id, key)

    if path and path.exists() and not body.regenerate:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass

    result = _generate(body.node, body.skill, body.language)
    if path:
        try:
            path.write_text(json.dumps(result), encoding="utf-8")
        except Exception:
            pass
    return result
