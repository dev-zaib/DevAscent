"""DeepSeek code evaluator — OpenAI-compatible, stdlib-only.

DeepSeek exposes an OpenAI-compatible chat API at https://api.deepseek.com.
We call it with urllib so there is no extra dependency (httpx/openai are not
in the venv). Used by the assessment API to give *real* AI evaluation of
submitted code instead of canned mock scores.

If no API key is configured, or the call fails, callers fall back to the
deterministic mock evaluator — the platform stays usable offline.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


class DeepSeekError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(os.getenv("DEEPSEEK_API_KEY"))


def _model() -> str:
    return os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


def _build_prompt(code: str, language: str, challenge: dict) -> str:
    rubric = challenge.get("rubric", {}) or {}
    rubric_lines = [
        f"- {skill} (weight {meta.get('weight', 0)}): {meta.get('description', '')}"
        for skill, meta in rubric.items()
    ]
    skills = ", ".join(rubric.keys()) or "code_quality"
    return f"""You are a ruthless but fair senior staff engineer grading a take-home.

CHALLENGE: {challenge.get('title', 'Untitled')}
{challenge.get('description', '')}

RUBRIC (score each dimension 0-100):
{chr(10).join(rubric_lines) or '- code_quality (weight 100): overall quality'}

CANDIDATE SUBMISSION ({language}):
```{language}
{code[:12000]}
```

Return ONLY valid JSON, no prose, in exactly this shape:
{{
  "rubric_scores": {{ {", ".join(f'"{s}": <0-100>' for s in (rubric.keys() or ['code_quality']))} }},
  "overall_score": <weighted 0-100>,
  "feedback": "<2-4 sentences: what works, the single most important gap, one concrete next step>",
  "strengths": ["..."],
  "gaps": ["..."]
}}
Dimensions to score: {skills}. Be specific and honest; reward correctness and production-readiness, penalize missing edge cases."""


def evaluate_code(
    code: str,
    language: str,
    challenge: dict,
    *,
    timeout: int = 60,
) -> dict:
    """Evaluate a submission with DeepSeek. Raises DeepSeekError on failure."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise DeepSeekError("DEEPSEEK_API_KEY not set")

    payload = {
        "model": _model(),
        "messages": [
            {"role": "system", "content": "You are a precise code-grading engine that replies only with JSON."},
            {"role": "user", "content": _build_prompt(code, language, challenge)},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:500]
        raise DeepSeekError(f"DeepSeek HTTP {e.code}: {detail}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise DeepSeekError(f"DeepSeek request failed: {e}") from e

    try:
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise DeepSeekError(f"Unparseable DeepSeek response: {e}") from e

    return _normalize(parsed, challenge)


def _chat(messages: list[dict], *, json_mode: bool = True, timeout: int = 60) -> str:
    """Low-level DeepSeek chat call. Returns the assistant message content."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise DeepSeekError("DEEPSEEK_API_KEY not set")
    payload = {
        "model": _model(),
        "messages": messages,
        "temperature": 0.3,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        raise DeepSeekError(f"DeepSeek HTTP {e.code}: {e.read().decode('utf-8','ignore')[:300]}") from e
    except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError) as e:
        raise DeepSeekError(f"DeepSeek request failed: {e}") from e


def teach(challenge: dict, language: str = "typescript", *, timeout: int = 60) -> dict:
    """Generate a focused lesson for a challenge — concepts, approach, scaffold.

    Teaches the *idea* and gives starter code, but deliberately NOT the full
    solution, so the user still learns by doing.
    """
    rubric = challenge.get("rubric", {}) or {}
    rubric_lines = "\n".join(
        f"- {s}: {m.get('description','')}" for s, m in rubric.items()
    )
    prompt = f"""A learner is stuck on this engineering challenge and wants to LEARN it before attempting.

CHALLENGE: {challenge.get('title','')}
{challenge.get('description','')}

GRADED ON:
{rubric_lines}

Teach it. Return ONLY valid JSON in exactly this shape:
{{
  "concept": "<2-3 sentence plain-English explanation of the core idea>",
  "key_points": ["<5-7 concrete things they must understand or implement>"],
  "approach_steps": ["<numbered, ordered steps to build the solution>"],
  "common_mistakes": ["<3-4 traps that lose points>"],
  "starter_code": "<a {language} scaffold with structure, signatures, and // TODO comments — NOT a complete working solution>",
  "study_terms": ["<3-5 things to google to go deeper>"]
}}
Be concrete and {language}-specific. The starter_code must compile-shaped but leave the hard logic as TODOs."""
    content = _chat(
        [
            {"role": "system", "content": "You are a patient senior engineer mentor. Reply only with JSON."},
            {"role": "user", "content": prompt},
        ],
        json_mode=True,
        timeout=timeout,
    )
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise DeepSeekError(f"Unparseable lesson: {e}") from e
    return {
        "concept": str(parsed.get("concept", "")).strip(),
        "key_points": parsed.get("key_points", []) or [],
        "approach_steps": parsed.get("approach_steps", []) or [],
        "common_mistakes": parsed.get("common_mistakes", []) or [],
        "starter_code": str(parsed.get("starter_code", "")),
        "study_terms": parsed.get("study_terms", []) or [],
        "provider": "deepseek",
    }


def _safe_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise DeepSeekError(f"Unparseable JSON: {e}") from e


def generate_roadmap(role: str, goal: str, skills_matrix: dict | None = None) -> dict:
    """Generate a personalized skill graph (roadmap) toward the goal level.

    Returns {nodes:[{id,label,tier,skill,deps,blurb}], edges:[{from,to}]}.
    """
    weak = ""
    if skills_matrix:
        ranked = sorted(skills_matrix.items(), key=lambda kv: kv[1])[:6]
        weak = "Current weak skills (prioritize early): " + ", ".join(
            f"{k} ({v:.0f}/100)" for k, v in ranked
        )
    prompt = f"""Design a personalized learning roadmap for an engineer.

CURRENT ROLE/LEVEL: {role}
GOAL: {goal or 'become a top 1% engineer'}
{weak}

Produce a dependency graph of 10-16 concrete skill nodes that takes them from where
they are to the goal. Order from fundamentals to advanced. Each node is a masterable
skill with prerequisites.

Return ONLY valid JSON:
{{
  "title": "<short roadmap title>",
  "nodes": [
    {{"id": "<slug>", "label": "<short skill name>", "tier": "<foundation|core|advanced|elite>",
      "skill": "<snake_case_skill_key>", "deps": ["<id>", ...], "blurb": "<one line why it matters>"}}
  ],
  "edges": [{{"from": "<id>", "to": "<id>"}}]
}}
Make deps form a sensible progression (foundation nodes have no deps). 12 nodes ideal."""
    parsed = _safe_json(_chat(
        [
            {"role": "system", "content": "You are a staff-engineer mentor designing learning paths. Reply only with JSON."},
            {"role": "user", "content": prompt},
        ],
        json_mode=True,
    ))
    nodes = parsed.get("nodes", []) or []
    edges = parsed.get("edges", []) or []
    # Derive edges from deps if the model omitted them.
    if not edges:
        edges = [{"from": d, "to": n["id"]} for n in nodes for d in (n.get("deps") or [])]
    return {"title": parsed.get("title", "Your roadmap"), "nodes": nodes, "edges": edges, "provider": "deepseek"}


def expand_node(label: str, skill: str = "", blurb: str = "") -> dict:
    """Break ONE roadmap skill into its deeper sub-skills (a sub-roadmap).

    Returns the same {title, nodes, edges} shape as generate_roadmap so the
    UI can drill in recursively. Leaf sub-skills are focused enough that a
    lesson and its interview cover the same scope.
    """
    prompt = f"""Break the engineering skill "{label}" into the concrete sub-skills needed to truly master it.
{f'Context: {blurb}' if blurb else ''}

Produce 6-10 FOCUSED sub-topics, ordered from prerequisite to advanced. Each must be specific
enough that one lesson + a short interview fully cover it (e.g. for "Programming Fundamentals":
Variables & Types, Operators, Control Flow, Loops, Functions, Scope & Closures, Arrays, Error Handling).

Return ONLY valid JSON:
{{
  "title": "{label}",
  "nodes": [{{"id": "<slug>", "label": "<focused sub-skill>", "tier": "<foundation|core|advanced|elite>",
    "skill": "<snake_case>", "deps": ["<id>"...], "blurb": "<one line>"}}],
  "edges": [{{"from": "<id>", "to": "<id>"}}]
}}
Foundation sub-skills have empty deps; later ones depend on earlier. 8 nodes ideal."""
    parsed = _safe_json(_chat(
        [
            {"role": "system", "content": "You decompose engineering skills into teachable sub-skills. Reply only with JSON."},
            {"role": "user", "content": prompt},
        ],
        json_mode=True,
    ))
    nodes = parsed.get("nodes", []) or []
    edges = parsed.get("edges", []) or []
    if not edges:
        edges = [{"from": d, "to": n["id"]} for n in nodes for d in (n.get("deps") or [])]
    return {"title": parsed.get("title", label), "nodes": nodes, "edges": edges, "provider": "deepseek"}


def generate_lesson(node_label: str, skill: str = "", language: str = "javascript") -> dict:
    """Generate an interactive, narratable lesson for a roadmap node."""
    prompt = f"""Create an engaging, interactive lesson for a self-learner.

TOPIC: {node_label}
SKILL KEY: {skill or node_label}
PREFERRED CODE LANGUAGE: {language}

Return ONLY valid JSON:
{{
  "concept": "<2-3 sentence plain-English core idea>",
  "narration_script": "<warm, spoken-style 120-200 word explanation to be read ALOUD; short sentences; no markdown>",
  "key_points": ["<5-7 must-know points>"],
  "approach_steps": ["<ordered steps to apply it>"],
  "visual_kind": "mermaid",
  "visual_spec": "<REQUIRED: a valid mermaid diagram (graph TD preferred) that maps the concept — 5-9 nodes showing the flow or relationships. Use simple quoted labels like A[\\"Label\\"]; no parentheses/colons/semicolons inside labels. This field must never be empty.>",
  "widget_html": "<a SMALL self-contained interactive HTML demo (<script> + minimal inline <style> only for layout, no external URLs) that lets the learner PLAY with this concept — sliders, buttons, a live visualization, animation, or step-through. Must run standalone in a sandboxed iframe.>",
  "study_terms": ["<3-5 terms to go deeper>"]
}}
widget_html rules: under ~3.5KB, dependency-free, NO external scripts/fonts. Use clean semantic HTML (h3, p, label, input, button) — the host page ALREADY provides the Inter font, a warm light background (#FBFAF7), and styled inputs/buttons in a clay/coral theme, so DO NOT set fonts, body background, or heavy colors; only add layout/positioning and the interactive logic. Prefer a real visual (animated canvas/SVG/DOM) over plain text. Make it genuinely fun to poke at."""
    parsed = _safe_json(_chat(
        [
            {"role": "system", "content": "You are an expert technical educator who makes concepts interactive. Reply only with JSON."},
            {"role": "user", "content": prompt},
        ],
        json_mode=True,
        timeout=90,
    ))
    return {
        "concept": str(parsed.get("concept", "")).strip(),
        "narration_script": str(parsed.get("narration_script", "")).strip(),
        "key_points": parsed.get("key_points", []) or [],
        "approach_steps": parsed.get("approach_steps", []) or [],
        "visual_kind": parsed.get("visual_kind", "none"),
        "visual_spec": str(parsed.get("visual_spec", "")),
        "widget_html": str(parsed.get("widget_html", "")),
        "study_terms": parsed.get("study_terms", []) or [],
        "provider": "deepseek",
    }


def interview_questions(node_label: str, skill: str = "", count: int = 4, learned: str = "") -> dict:
    """Generate interview questions scoped to what the learner was actually taught."""
    scope = (
        f"\nThe learner just studied this material — ask ONLY about what it covered, nothing beyond it:\n{learned}\n"
        if learned else ""
    )
    prompt = f"""Act as a senior interviewer. Produce {count} interview questions on:

TOPIC: {node_label} (skill: {skill or node_label}){scope}

Mix conceptual and applied, but stay strictly within the taught scope above (if given).
Return ONLY valid JSON:
{{"questions": [{{"id": <int>, "type": "<concept|coding>", "prompt": "<question>",
  "what_we_look_for": "<1 line of what a strong answer shows>"}}]}}"""
    parsed = _safe_json(_chat(
        [
            {"role": "system", "content": "You are a rigorous technical interviewer. Reply only with JSON."},
            {"role": "user", "content": prompt},
        ],
        json_mode=True,
    ))
    return {"questions": parsed.get("questions", []) or [], "provider": "deepseek"}


def assess_questions(topics: list[str], count: int = 6) -> dict:
    """Cross-topic assessment over ONLY the topics the learner has completed."""
    topic_list = "\n".join(f"- {t}" for t in topics) or "- general engineering"
    prompt = f"""The learner has completed these topics. Assess ONLY these — do not ask about anything else:
{topic_list}

Produce {count} interview questions spread across the completed topics (mix concept + applied),
hardest last. Return ONLY valid JSON:
{{"questions": [{{"id": <int>, "type": "<concept|coding>", "prompt": "<question>",
  "what_we_look_for": "<1 line>", "topic": "<which completed topic>"}}]}}"""
    parsed = _safe_json(_chat(
        [
            {"role": "system", "content": "You are a rigorous technical interviewer. Reply only with JSON."},
            {"role": "user", "content": prompt},
        ],
        json_mode=True,
    ))
    return {"questions": parsed.get("questions", []) or [], "provider": "deepseek"}


def grade_answer(question: str, answer: str, *, what_we_look_for: str = "") -> dict:
    """Grade a single interview answer 0-100 with feedback."""
    prompt = f"""Grade this interview answer like a fair senior interviewer.

QUESTION: {question}
{f'STRONG ANSWER SHOWS: {what_we_look_for}' if what_we_look_for else ''}

CANDIDATE ANSWER:
{answer[:6000]}

Return ONLY valid JSON:
{{"score": <0-100>, "feedback": "<2-3 sentences: what was right, the key gap, one improvement>",
  "verdict": "<strong|adequate|weak>"}}"""
    parsed = _safe_json(_chat(
        [
            {"role": "system", "content": "You grade interview answers precisely. Reply only with JSON."},
            {"role": "user", "content": prompt},
        ],
        json_mode=True,
    ))
    try:
        score = max(0.0, min(100.0, float(parsed.get("score", 0))))
    except (TypeError, ValueError):
        score = 0.0
    return {
        "score": round(score, 2),
        "feedback": str(parsed.get("feedback", "")).strip() or "Graded.",
        "verdict": parsed.get("verdict", "adequate"),
        "provider": "deepseek",
    }


def _normalize(parsed: dict, challenge: dict) -> dict:
    """Coerce model output into the canonical evaluation dict."""
    rubric = challenge.get("rubric", {}) or {}
    raw_scores = parsed.get("rubric_scores", {}) or {}

    rubric_scores: dict[str, float] = {}
    for skill in (rubric.keys() or raw_scores.keys()):
        val = raw_scores.get(skill, 0)
        try:
            rubric_scores[skill] = max(0.0, min(100.0, float(val)))
        except (TypeError, ValueError):
            rubric_scores[skill] = 0.0

    # Weighted overall if the model didn't give a sane one.
    overall = parsed.get("overall_score")
    try:
        overall = float(overall)
    except (TypeError, ValueError):
        overall = None
    if overall is None or not (0 <= overall <= 100):
        total_w = sum((rubric.get(s, {}) or {}).get("weight", 1) for s in rubric_scores) or 1
        overall = round(
            sum(rubric_scores[s] * (rubric.get(s, {}) or {}).get("weight", 1) for s in rubric_scores)
            / total_w,
            2,
        )

    feedback = str(parsed.get("feedback", "")).strip() or "Evaluation complete."
    return {
        "score": round(float(overall), 2),
        "rubric_breakdown": {k: round(v, 2) for k, v in rubric_scores.items()},
        "ai_feedback": feedback,
        "strengths": parsed.get("strengths", []) or [],
        "gaps": parsed.get("gaps", []) or [],
        "provider": "deepseek",
    }
