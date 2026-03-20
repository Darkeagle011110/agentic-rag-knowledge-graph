"""
Schema construction proposal tools for structured data (Lesson 6).
"""
from __future__ import annotations

from typing import Any

from google.adk.tools import ToolContext

from neo4j_client import tool_success, tool_error
from tools.file_tools import search_file

PROPOSED_CONSTRUCTION_PLAN = "proposed_construction_plan"
APPROVED_CONSTRUCTION_PLAN = "approved_construction_plan"
APPROVED_FILES = "approved_files"
SUGGESTED_FILES = "suggested_files"

# ──────────────────────────────────────────────────────────
# File approval
# ──────────────────────────────────────────────────────────

def get_approved_files(tool_context: ToolContext) -> dict:
    """Gets the list of approved files from state."""
    files = tool_context.state.get(APPROVED_FILES, [])
    return tool_success(APPROVED_FILES, files)


def set_suggested_files(suggest_files: list[str], tool_context: ToolContext) -> dict:
    """Sets the list of suggested files for data import."""
    tool_context.state[SUGGESTED_FILES] = suggest_files
    return tool_success(SUGGESTED_FILES, suggest_files)


def get_suggested_files(tool_context: ToolContext) -> dict:
    """Gets the current list of suggested files."""
    return tool_success(SUGGESTED_FILES, tool_context.state.get(SUGGESTED_FILES, []))


def approve_suggested_files(tool_context: ToolContext) -> dict:
    """Approves suggested_files → approved_files. Only call after explicit user approval."""
    if SUGGESTED_FILES not in tool_context.state:
        return tool_error("No suggested files to approve. Set suggested files first.")
    tool_context.state[APPROVED_FILES] = tool_context.state[SUGGESTED_FILES]
    return tool_success(APPROVED_FILES, tool_context.state[APPROVED_FILES])


# ──────────────────────────────────────────────────────────
# Construction plan
# ──────────────────────────────────────────────────────────

def propose_node_construction(
    approved_file: str,
    proposed_label: str,
    unique_column_name: str,
    proposed_properties: list[str],
    tool_context: ToolContext,
) -> dict:
    """Proposes a node construction rule for an approved file.

    Args:
        approved_file: File to create nodes from.
        proposed_label: Neo4j label for the nodes.
        unique_column_name: Column whose values uniquely identify each node.
        proposed_properties: Other column names to import as node properties.
    """
    sanity = search_file(approved_file, unique_column_name)
    if sanity["status"] == "error":
        return sanity
    if sanity["search_results"]["metadata"]["lines_found"] == 0:
        return tool_error(
            f"{approved_file} has no column '{unique_column_name}'. "
            "Check file content and try again."
        )

    plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    rule = {
        "construction_type": "node",
        "source_file": approved_file,
        "label": proposed_label,
        "unique_column_name": unique_column_name,
        "properties": proposed_properties,
    }
    plan[proposed_label] = rule
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = plan
    return tool_success("node_construction", rule)


def propose_relationship_construction(
    approved_file: str,
    proposed_relationship_type: str,
    from_node_label: str,
    from_node_column: str,
    to_node_label: str,
    to_node_column: str,
    proposed_properties: list[str],
    tool_context: ToolContext,
) -> dict:
    """Proposes a relationship construction rule for an approved file."""
    for col in (from_node_column, to_node_column):
        check = search_file(approved_file, col)
        if check["status"] == "error" or check["search_results"]["metadata"]["lines_found"] == 0:
            return tool_error(
                f"{approved_file} does not have column '{col}'. "
                "Check file content and reconsider the relationship."
            )

    plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    rule = {
        "construction_type": "relationship",
        "source_file": approved_file,
        "relationship_type": proposed_relationship_type,
        "from_node_label": from_node_label,
        "from_node_column": from_node_column,
        "to_node_label": to_node_label,
        "to_node_column": to_node_column,
        "properties": proposed_properties,
    }
    plan[proposed_relationship_type] = rule
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = plan
    return tool_success("relationship_construction", rule)


def remove_node_construction(node_label: str, tool_context: ToolContext) -> dict:
    """Removes a node construction rule from the proposed plan."""
    plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    if node_label not in plan:
        return tool_success("node_construction_removed", "not found — no action needed")
    del plan[node_label]
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = plan
    return tool_success("node_construction_removed", node_label)


def remove_relationship_construction(relationship_type: str, tool_context: ToolContext) -> dict:
    """Removes a relationship construction rule from the proposed plan."""
    plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    plan.pop(relationship_type, None)
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = plan
    return tool_success("relationship_construction_removed", relationship_type)


def get_proposed_construction_plan(tool_context: ToolContext) -> dict:
    """Gets the current proposed construction plan."""
    return tool_success(PROPOSED_CONSTRUCTION_PLAN, tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {}))


def approve_proposed_construction_plan(tool_context: ToolContext) -> dict:
    """Approves the proposed construction plan. Only call after explicit user approval."""
    if PROPOSED_CONSTRUCTION_PLAN not in tool_context.state:
        return tool_error("No proposed construction plan found. Propose a plan first.")
    tool_context.state[APPROVED_CONSTRUCTION_PLAN] = tool_context.state[PROPOSED_CONSTRUCTION_PLAN]
    return tool_success(APPROVED_CONSTRUCTION_PLAN, tool_context.state[APPROVED_CONSTRUCTION_PLAN])
