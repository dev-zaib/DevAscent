"""LangGraph assessment state graph.

Graph flow:
  InitializeAssessment → PresentChallenge → [user submits code]
  EvaluateSubmission → UpdateSkillsMatrix → DetermineNextStep →
    → EscalateChallenge (if >= 85%) → back to EvaluateSubmission
    → LevelAdvance (if >= 85% AND escalation_depth >= 3)
    → KeepLevel (if >= 70%)
    → Reinforce (if < 70%)
    → FlagReview (if < 40%)
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from devascent.assessment.state import DevAscentState
from devascent.assessment.nodes.initialize import initialize_assessment
from devascent.assessment.nodes.present import present_challenge
from devascent.assessment.nodes.evaluate import evaluate_submission
from devascent.assessment.nodes.update_skills import update_skills_matrix
from devascent.assessment.nodes.determine_next import determine_next_step
from devascent.assessment.nodes.escalate import escalate_challenge
from devascent.assessment.router import route_after_determine
from devascent.config import assessment_config


def build_assessment_graph() -> StateGraph:
    graph = StateGraph(DevAscentState)

    graph.add_node("initialize", initialize_assessment)
    graph.add_node("present_challenge", present_challenge)
    graph.add_node("evaluate", evaluate_submission)
    graph.add_node("update_skills", update_skills_matrix)
    graph.add_node("determine_next", determine_next_step)
    graph.add_node("escalate", escalate_challenge)

    graph.set_entry_point("initialize")
    graph.add_edge("initialize", "present_challenge")
    graph.add_edge("present_challenge", "evaluate")
    graph.add_edge("evaluate", "update_skills")
    graph.add_edge("update_skills", "determine_next")

    graph.add_conditional_edges(
        "determine_next",
        route_after_determine,
        {
            "escalate": "escalate",
            "present_challenge": "present_challenge",
            "__end__": END,
        },
    )

    graph.add_edge("escalate", "present_challenge")

    return graph


def compile_graph():
    graph = build_assessment_graph()
    checkpointer = PostgresSaver.from_conn_string(assessment_config.database_url)
    return graph.compile(checkpointer=checkpointer)


# Module-level compiled graph — lazy-initialized
_compiled_graph: StateGraph | None = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = compile_graph()
    return _compiled_graph
