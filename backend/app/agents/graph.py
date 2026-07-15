from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    analyze_safety_node,
    build_fallback_node,
    build_safety_redirect_node,
    build_supportive_response_node,
    finalize_response_node,
    generate_routine_node,
    increment_retry_node,
    initialize_state_node,
    retrieve_history_node,
    retrieve_sleep_knowledge_node,
    route_after_safety,
    route_after_safety_check,
    safety_check_node,
)
from app.agents.state import AgentState


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("initialize_state", initialize_state_node)
    workflow.add_node("analyze_safety", analyze_safety_node)
    workflow.add_node("build_safety_redirect", build_safety_redirect_node)
    workflow.add_node("build_supportive_response", build_supportive_response_node)
    workflow.add_node("retrieve_history", retrieve_history_node)
    workflow.add_node("retrieve_sleep_knowledge", retrieve_sleep_knowledge_node)
    workflow.add_node("generate_routine", generate_routine_node)
    workflow.add_node("safety_check", safety_check_node)
    workflow.add_node("increment_retry", increment_retry_node)
    workflow.add_node("build_fallback", build_fallback_node)
    workflow.add_node("finalize_response", finalize_response_node)

    workflow.add_edge(START, "initialize_state")
    workflow.add_edge("initialize_state", "analyze_safety")

    workflow.add_conditional_edges(
        "analyze_safety",
        route_after_safety,
        {
            "crisis": "build_safety_redirect",
            "distress": "build_supportive_response",
            "none": "retrieve_history",
        },
    )

    workflow.add_edge("build_safety_redirect", "finalize_response")
    workflow.add_edge("build_supportive_response", "finalize_response")
    workflow.add_edge("retrieve_history", "retrieve_sleep_knowledge")
    workflow.add_edge("retrieve_sleep_knowledge", "generate_routine")
    workflow.add_edge("generate_routine", "safety_check")

    workflow.add_conditional_edges(
        "safety_check",
        route_after_safety_check,
        {
            "pass": "finalize_response",
            "retry": "increment_retry",
            "fallback": "build_fallback",
        },
    )

    workflow.add_edge("increment_retry", "generate_routine")
    workflow.add_edge("build_fallback", "finalize_response")
    workflow.add_edge("finalize_response", END)

    return workflow.compile()
