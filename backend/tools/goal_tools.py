"""
Goal-related tools for the User Intent agent (Lesson 4).
"""
from __future__ import annotations

from google.adk.tools import ToolContext

from neo4j_client import tool_success, tool_error

PERCEIVED_USER_GOAL = "perceived_user_goal"
APPROVED_USER_GOAL = "approved_user_goal"


def set_perceived_user_goal(
    kind_of_graph: str,
    graph_description: str,
    tool_context: ToolContext,
) -> dict:
    """Sets the perceived user's goal (kind of graph + description).

    Args:
        kind_of_graph: 2-3 word definition of the graph, e.g. "supply chain analysis"
        graph_description: Single-paragraph description of the user's intent.
    """
    user_goal = {"kind_of_graph": kind_of_graph, "graph_description": graph_description}
    tool_context.state[PERCEIVED_USER_GOAL] = user_goal
    return tool_success(PERCEIVED_USER_GOAL, user_goal)


def approve_perceived_user_goal(tool_context: ToolContext) -> dict:
    """Upon user approval, promotes perceived_user_goal → approved_user_goal.

    Only call this if the user has explicitly approved.
    """
    if PERCEIVED_USER_GOAL not in tool_context.state:
        return tool_error(
            "perceived_user_goal not set. "
            "Set perceived user goal first, or ask clarifying questions."
        )
    tool_context.state[APPROVED_USER_GOAL] = tool_context.state[PERCEIVED_USER_GOAL]
    return tool_success(APPROVED_USER_GOAL, tool_context.state[APPROVED_USER_GOAL])


def get_approved_user_goal(tool_context: ToolContext) -> dict:
    """Retrieves the approved user goal from state."""
    goal = tool_context.state.get(APPROVED_USER_GOAL)
    if not goal:
        return tool_error(
            "No approved user goal found in state. "
            "Complete the user-intent step first."
        )
    return tool_success(APPROVED_USER_GOAL, goal)
