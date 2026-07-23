from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes import (
    retrieve_memories_node,
    parse_intent_node,
    ask_clarification_node,
    resolve_entities_node,
    confirm_action_node,
    execute_tool_node,
    respond_node,
    handle_error_node,
    SIDE_EFFECTING_TOOLS,
)


def route_after_parse(state: AgentState) -> str:
    """Routing logic after intent parsing."""
    if state.get("missing_slots"):
        return "ask_clarification"
    
    intent = state.get("intent")
    if intent in SIDE_EFFECTING_TOOLS and not state.get("confirmation_given"):
        return "confirm_action"
    
    if state.get("tool_name"):
        return "execute_tool"
    
    return "respond"


def route_after_confirm(state: AgentState) -> str:
    """Routing logic after confirmation request node."""
    if state.get("confirmation_given") is True:
        return "execute_tool"
    elif state.get("confirmation_given") is False:
        return "respond"
    # If waiting for user confirmation response, stop graph execution
    return END


def build_agent_graph():
    """Builds and compiles the stateful LangGraph Agent graph."""
    workflow = StateGraph(AgentState)

    # 1. Add Nodes
    workflow.add_node("retrieve_memories", retrieve_memories_node)
    workflow.add_node("parse_intent", parse_intent_node)
    workflow.add_node("ask_clarification", ask_clarification_node)
    workflow.add_node("resolve_entities", resolve_entities_node)
    workflow.add_node("confirm_action", confirm_action_node)
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("respond", respond_node)

    # 2. Set Entry Point
    workflow.set_entry_point("retrieve_memories")

    # 3. Add Edges
    workflow.add_edge("retrieve_memories", "parse_intent")

    # Conditional branching after parse_intent
    workflow.add_conditional_edges(
        "parse_intent",
        route_after_parse,
        {
            "ask_clarification": "ask_clarification",
            "confirm_action": "confirm_action",
            "execute_tool": "execute_tool",
            "respond": "respond",
        }
    )

    workflow.add_edge("ask_clarification", END)
    
    workflow.add_conditional_edges(
        "confirm_action",
        route_after_confirm,
        {
            "execute_tool": "execute_tool",
            "respond": "respond",
            END: END,
        }
    )

    workflow.add_edge("execute_tool", "respond")
    workflow.add_edge("respond", END)

    return workflow.compile()

# Singleton compiled graph instance
agent_graph = build_agent_graph()
