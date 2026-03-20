"""
User Intent Agent — Lesson 4.
Helps the user ideate a knowledge graph use case through conversation.
"""
from __future__ import annotations

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from tools.goal_tools import set_perceived_user_goal, approve_perceived_user_goal


def build_user_intent_agent(model_name: str = "openai/gpt-4o") -> Agent:
    llm = LiteLlm(model=model_name)

    instruction = """
    You are an expert at knowledge graph use cases.
    Your primary goal is to help the user come up with a knowledge graph use case.

    If the user is unsure what to do, make some suggestions based on classic use cases like:
    - social network involving friends, family, or professional relationships
    - logistics network with suppliers, customers, and partners
    - recommendation system with customers, products, and purchase patterns
    - fraud detection over multiple accounts with suspicious patterns of transactions
    - pop-culture graphs with movies, books, or music
    - supply chain / bill-of-materials with products, assemblies, parts and suppliers

    A user goal has two components:
    - kind_of_graph: at most 3 words describing the graph, e.g. "social network" or "supply chain"
    - description: a few sentences about the intention of the graph

    Think carefully and collaborate with the user:
    1. Understand the user's goal (kind_of_graph + description)
    2. Ask clarifying questions as needed
    3. When you understand their goal, use 'set_perceived_user_goal' to record your perception
    4. Present the perceived goal to the user for confirmation
    5. If the user agrees, use 'approve_perceived_user_goal' to finalise. This saves the goal
       under 'approved_user_goal' in state.
    """

    return Agent(
        name="user_intent_agent_v1",
        model=llm,
        description="Helps the user ideate on a knowledge graph use case.",
        instruction=instruction,
        tools=[set_perceived_user_goal, approve_perceived_user_goal],
    )
