"""Interview / Test API — prove a roadmap node.

POST /api/interview/start  {node, skill?, count?} -> questions
POST /api/interview/grade  {user_id?, node?, skill?, question, answer, what_we_look_for?}
     -> score + feedback; writes a journal entry so the coach + roadmap update.
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["interview"])


class StartRequest(BaseModel):
    node: str
    skill: str = ""
    count: int = 4
    learned: str = ""  # taught content (concept + key points) to scope questions


class GradeRequest(BaseModel):
    question: str
    answer: str
    what_we_look_for: str = ""
    user_id: str | None = None
    node: str = ""
    skill: str = ""


def _mock_questions(node: str, count: int) -> dict:
    base = [
        {"id": 1, "type": "concept", "prompt": f"Explain {node} in your own words, and when you'd use it.", "what_we_look_for": "Clear mental model"},
        {"id": 2, "type": "concept", "prompt": f"What are the main trade-offs or failure modes of {node}?", "what_we_look_for": "Awareness of pitfalls"},
        {"id": 3, "type": "coding", "prompt": f"Sketch an implementation or usage of {node}. Walk through edge cases.", "what_we_look_for": "Correct, handles edges"},
        {"id": 4, "type": "concept", "prompt": f"How does {node} behave under scale or load?", "what_we_look_for": "Production thinking"},
    ]
    return {"questions": base[:count], "provider": "mock"}


def _mock_grade(answer: str) -> dict:
    n = len(answer.strip())
    score = 35 if n < 40 else 62 if n < 200 else 78
    return {
        "score": score,
        "feedback": "Offline demo grade. Set DEEPSEEK_API_KEY for real grading. Add specifics, edge cases, and trade-offs to score higher.",
        "verdict": "adequate" if score >= 60 else "weak",
        "provider": "mock",
    }


@router.post("/start")
def start(body: StartRequest) -> dict:
    try:
        from devascent.llm import deepseek
        if deepseek.is_configured():
            return deepseek.interview_questions(body.node, body.skill, body.count, body.learned)
    except Exception:
        pass
    return _mock_questions(body.node, body.count)


class AssessRequest(BaseModel):
    user_id: str
    count: int = 6


@router.post("/assess")
def assess(body: AssessRequest) -> dict:
    """Assessment over ONLY the topics the learner has marked complete."""
    # Read completed topics.
    topics: list[str] = []
    try:
        from devascent.api.routes.progress import _read
        topics = [v.get("label", k) for k, v in _read(body.user_id).items()]
    except Exception:
        topics = []
    if not topics:
        return {"questions": [], "provider": "none", "reason": "no_completed_topics"}
    try:
        from devascent.llm import deepseek
        if deepseek.is_configured():
            return deepseek.assess_questions(topics, body.count)
    except Exception:
        pass
    # Mock: one question per topic.
    return {"questions": [
        {"id": i + 1, "type": "concept", "prompt": f"Explain {t} and a real-world use.",
         "what_we_look_for": "Clear understanding", "topic": t}
        for i, t in enumerate(topics[:body.count])
    ], "provider": "mock"}


@router.post("/grade")
def grade(body: GradeRequest) -> dict:
    result = None
    try:
        from devascent.llm import deepseek
        if deepseek.is_configured():
            result = deepseek.grade_answer(body.question, body.answer, what_we_look_for=body.what_we_look_for)
    except Exception:
        result = None
    if result is None:
        result = _mock_grade(body.answer)

    # Persist to the durable journal so coach + roadmap reflect the result.
    if body.user_id and (body.skill or body.node):
        try:
            from devascent.coach.journal import JournalEntry, LearningJournal
            from devascent.coach.coach import build_coach_report
            from devascent.coach.memory_bridge import write_progress_memory
            skill = body.skill or body.node
            LearningJournal(body.user_id).append(JournalEntry(
                challenge_id=f"interview:{body.node or skill}",
                level="INTERVIEW",
                score=float(result["score"]),
                rubric_scores={skill: float(result["score"])},
                ai_feedback=result.get("feedback", ""),
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))
            report = build_coach_report(body.user_id, LearningJournal(body.user_id).read_all())
            write_progress_memory(report)
        except Exception:
            pass
    return result
