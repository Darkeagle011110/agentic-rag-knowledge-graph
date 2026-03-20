"""
NER + Fact Extraction agents for unstructured data — Lesson 7.
"""
from __future__ import annotations

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import ToolContext

from neo4j_client import tool_success, tool_error
from tools.goal_tools import get_approved_user_goal
from tools.schema_tools import get_approved_files
from tools.file_tools import sample_file

# ─── State keys ───────────────────────────────────────────
PROPOSED_ENTITIES = "proposed_entity_types"
APPROVED_ENTITIES = "approved_entity_types"
PROPOSED_FACTS = "proposed_fact_types"
APPROVED_FACTS = "approved_fact_types"


# ─── NER tools ────────────────────────────────────────────

def get_well_known_types(tool_context: ToolContext) -> dict:
    """Gets well-known node labels from the approved construction plan."""
    plan = tool_context.state.get("approved_construction_plan", {})
    labels = {e["label"] for e in plan.values() if e.get("construction_type") == "node"}
    return tool_success("approved_labels", list(labels))


def set_proposed_entities(proposed_entity_types: list[str], tool_context: ToolContext) -> dict:
    """Sets the list of entity types proposed for extraction from unstructured text."""
    tool_context.state[PROPOSED_ENTITIES] = proposed_entity_types
    return tool_success(PROPOSED_ENTITIES, proposed_entity_types)


def get_proposed_entities(tool_context: ToolContext) -> dict:
    """Gets the currently proposed entity types."""
    return tool_success(PROPOSED_ENTITIES, tool_context.state.get(PROPOSED_ENTITIES, []))


def approve_proposed_entities(tool_context: ToolContext) -> dict:
    """Approves proposed entity types. Only call after explicit user approval."""
    if PROPOSED_ENTITIES not in tool_context.state:
        return tool_error("No proposed entities. Set them first, then call after user approval.")
    tool_context.state[APPROVED_ENTITIES] = tool_context.state[PROPOSED_ENTITIES]
    return tool_success(APPROVED_ENTITIES, tool_context.state[APPROVED_ENTITIES])


def get_approved_entities(tool_context: ToolContext) -> dict:
    """Gets the approved list of entity types."""
    return tool_success(APPROVED_ENTITIES, tool_context.state.get(APPROVED_ENTITIES, []))


# ─── Fact tools ───────────────────────────────────────────

def add_proposed_fact(
    approved_subject_label: str,
    proposed_predicate_label: str,
    approved_object_label: str,
    tool_context: ToolContext,
) -> dict:
    """Adds a proposed fact type (subject, predicate, object triple).

    Args:
        approved_subject_label: Must be an approved entity type.
        proposed_predicate_label: Relationship label extracted from source text.
        approved_object_label: Must be an approved entity type.
    """
    approved = tool_context.state.get(APPROVED_ENTITIES, [])
    if approved_subject_label not in approved:
        return tool_error(f"Subject '{approved_subject_label}' is not in approved entities.")
    if approved_object_label not in approved:
        return tool_error(f"Object '{approved_object_label}' is not in approved entities.")

    facts = tool_context.state.get(PROPOSED_FACTS, {})
    facts[proposed_predicate_label] = {
        "subject_label": approved_subject_label,
        "predicate_label": proposed_predicate_label,
        "object_label": approved_object_label,
    }
    tool_context.state[PROPOSED_FACTS] = facts
    return tool_success(PROPOSED_FACTS, facts)


def get_proposed_facts(tool_context: ToolContext) -> dict:
    """Gets all proposed fact types."""
    return tool_success(PROPOSED_FACTS, tool_context.state.get(PROPOSED_FACTS, {}))


def approve_proposed_facts(tool_context: ToolContext) -> dict:
    """Approves proposed fact types. Only call after explicit user approval."""
    if PROPOSED_FACTS not in tool_context.state:
        return tool_error("No proposed facts to approve.")
    tool_context.state[APPROVED_FACTS] = tool_context.state[PROPOSED_FACTS]
    return tool_success(APPROVED_FACTS, tool_context.state[APPROVED_FACTS])


# ─── Agent builders ───────────────────────────────────────

def build_ner_agent(model_name: str = "openai/gpt-4o") -> Agent:
    llm = LiteLlm(model=model_name)

    instruction = """
    You are a top-tier algorithm designed for analyzing text files and proposing
    the kind of named entities that could be extracted which are relevant to the user's goal.

    Entities are people, places, things and qualities — NOT quantities.

    Two approaches:
    - Well-known entities: closely match existing node labels in the approved construction plan
    - Discovered entities: consistently appear in the text and support the user's goal

    Rules:
    - Always reuse well-known entity types when applicable
    - Discovered entities must appear consistently in the source text
    - Do not propose purely quantitative types (e.g., "Age") — those are properties

    Prepare:
    - get_approved_user_goal
    - get_approved_files
    - get_well_known_types

    Steps:
    1. Sample unstructured files using sample_file
    2. Identify well-known + discovered entity types
    3. Call set_proposed_entities to save your proposal
    4. Present to user and ask for approval
    5. On approval, call approve_proposed_entities
    """

    return Agent(
        name="ner_schema_agent_v1",
        description="Proposes named entity types to extract from unstructured text files.",
        model=llm,
        instruction=instruction,
        tools=[
            get_approved_user_goal, get_approved_files, sample_file,
            get_well_known_types,
            set_proposed_entities, get_proposed_entities, approve_proposed_entities,
        ],
    )


def build_fact_extraction_agent(model_name: str = "openai/gpt-4o") -> Agent:
    llm = LiteLlm(model=model_name)

    instruction = """
    You are a top-tier algorithm designed for analyzing text files and proposing
    the type of facts (subject, predicate, object triples) that can be extracted
    which are relevant to the user's goal.

    Do NOT propose specific facts, only the general TYPES of facts.
    Example: propose "(Product, has_issue, Issue)" not "(Stockholm Chair, has_issue, wobbly leg)"

    Rules:
    - Only use APPROVED entity types as subject and object
    - The predicate must appear in the source text
    - Focus on predicates relevant to the user's goal

    Prepare:
    - get_approved_user_goal
    - get_approved_files
    - get_approved_entities

    Steps:
    1. Sample some approved files with sample_file
    2. Identify how entities relate in the text
    3. Call add_proposed_fact for each fact type
    4. Call get_proposed_facts and present to user
    5. On approval, call approve_proposed_facts
    """

    return Agent(
        name="fact_type_extraction_agent_v1",
        description="Proposes fact types (SPO triples) for extraction from unstructured text.",
        model=llm,
        instruction=instruction,
        tools=[
            get_approved_user_goal, get_approved_files,
            get_approved_entities,
            sample_file,
            add_proposed_fact, get_proposed_facts, approve_proposed_facts,
        ],
    )
