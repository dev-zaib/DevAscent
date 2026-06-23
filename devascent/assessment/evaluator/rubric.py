"""Scoring rubric engine — evaluates submissions against challenge criteria."""
import json


class RubricDimension:
    def __init__(self, name: str, weight: float, description: str):
        self.name = name
        self.weight = weight
        self.description = description


class RubricEngine:
    def __init__(self, rubric_spec: dict):
        self.dimensions = [
            RubricDimension(name, spec["weight"], spec["description"])
            for name, spec in rubric_spec.items()
        ]
        self.weights = {d.name: d.weight for d in self.dimensions}

    def compute_score(self, dimension_scores: dict[str, float]) -> float:
        """Compute weighted total score from individual dimension scores."""
        total = 0.0
        for dim in self.dimensions:
            score = dimension_scores.get(dim.name, 0)
            total += score * (dim.weight / 100.0)
        return round(total, 2)

    def to_prompt_context(self) -> str:
        """Generate LLM prompt context describing rubric dimensions."""
        lines = []
        for dim in self.dimensions:
            lines.append(
                f"- {dim.name} (weight: {dim.weight}%): {dim.description}"
            )
        return "\n".join(lines)


def build_evaluation_prompt(
    challenge: dict, code: str, language: str, rubric: RubricEngine
) -> str:
    return f"""You are evaluating a submitted solution for an engineering assessment challenge.

CHALLENGE:
{challenge.get('title', 'Unknown Challenge')}
{challenge.get('description', '')}

SUBMITTED CODE ({language}):
```{language}
{code}
```

RUBRIC (score each dimension 0-100):
{rubric.to_prompt_context()}

Return your evaluation as a JSON object with:
1. "scores": dict mapping dimension names to numeric scores (0-100)
2. "feedback": brief feedback per dimension
3. "overall_notes": summary of what was done well and what needs improvement

Respond ONLY with valid JSON, no markdown wrapping."""


def parse_evaluation_response(response_text: str) -> dict:
    """Parse LLM evaluation response into structured scores."""
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text)
