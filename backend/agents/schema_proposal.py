"""
Schema Proposal + Critic agents — Lesson 6.
A LoopAgent pairs a proposal agent with a critic agent to refine the construction plan.
"""
from __future__ import annotations

from google.adk.agents import LlmAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.base_agent import BaseAgent
from google.adk.events import Event, EventActions
from google.adk.models.lite_llm import LiteLlm
from typing import AsyncGenerator

from tools.goal_tools import get_approved_user_goal
from tools.schema_tools import (
    get_approved_files,
    get_proposed_construction_plan,
    propose_node_construction,
    propose_relationship_construction,
    remove_node_construction,
    remove_relationship_construction,
    approve_proposed_construction_plan,
)
from tools.file_tools import sample_file, search_file


# ──────────────────────────────────────────────────────────
# CheckStatusAndEscalate — stops the LoopAgent when critic says "valid"
# ──────────────────────────────────────────────────────────

class CheckStatusAndEscalate(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        feedback = ctx.session.state.get("feedback", "valid")
        should_stop = feedback.strip().lower() == "valid"
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))


# ──────────────────────────────────────────────────────────
# Build the agents
# ──────────────────────────────────────────────────────────

def build_schema_refinement_loop(model_name: str = "openai/gpt-4o") -> LoopAgent:
    llm = LiteLlm(model=model_name)

    # ── Proposal agent ─────────────────────────────────
    proposal_instruction = """
    You are an expert at knowledge graph modeling with property graphs.
    Propose an appropriate schema by specifying construction rules which transform
    approved files into nodes or relationships. The resulting schema should describe
    a knowledge graph based on the user goal.

    Consider feedback if available:
    <feedback>
    {feedback}
    </feedback>

    Every file in the approved files list will become either a node or a relationship.
    Guidance:
    - If the file name is singular with one unique ID → it is likely a node
    - If the file name combines two entities → it is a full relationship file
    - If a node file contains foreign keys → those become reference relationships

    Prepare:
    - get_approved_user_goal
    - get_approved_files
    - get_proposed_construction_plan (check existing state)

    For each approved file:
    1. Inspect with sample_file and search_file
    2. Decide node vs. relationship
    3. Call propose_node_construction or propose_relationship_construction
    4. When done, call get_proposed_construction_plan to present to user
    """

    proposal_agent = LlmAgent(
        name="schema_proposal_agent_v1",
        description="Proposes a knowledge graph schema based on user goal and approved files.",
        model=llm,
        instruction=proposal_instruction,
        tools=[
            get_approved_user_goal, get_approved_files,
            get_proposed_construction_plan,
            sample_file, search_file,
            propose_node_construction, propose_relationship_construction,
            remove_node_construction, remove_relationship_construction,
        ],
    )

    # ── Critic agent ────────────────────────────────────
    critic_instruction = """
    You are an expert at knowledge graph modeling with property graphs.
    Criticize the proposed schema for relevance to the user goal and approved files.

    Checks to perform:
    - Are unique identifiers truly unique? Use search_file to validate.
    - Could any nodes actually be relationships?
    - Is every node connected to at least one other node?
    - Are hierarchical relationships missing?
    - Are there redundant relationships?

    Prepare:
    - get_approved_user_goal
    - get_approved_files
    - get_proposed_construction_plan
    - use sample_file and search_file to validate

    If the schema looks good respond with exactly one word: valid
    If it has problems respond with: retry
    followed by a concise bullet list of issues.
    """

    critic_agent = LlmAgent(
        name="schema_critic_agent_v1",
        description="Critiques the proposed schema and provides actionable feedback.",
        model=llm,
        instruction=critic_instruction,
        tools=[
            get_approved_user_goal, get_approved_files,
            get_proposed_construction_plan,
            sample_file, search_file,
        ],
        output_key="feedback",  # auto-saved to session state
    )

    return LoopAgent(
        name="schema_refinement_loop",
        description="Iteratively proposes and critiques a graph schema until valid.",
        max_iterations=3,
        sub_agents=[
            proposal_agent,
            critic_agent,
            CheckStatusAndEscalate(name="StopChecker"),
        ],
    )
