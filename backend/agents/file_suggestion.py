"""
File Suggestion Agent — Lesson 5.
Reads approved_user_goal and recommends data files for KG construction.
"""
from __future__ import annotations

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from tools.goal_tools import get_approved_user_goal
from tools.schema_tools import (
    set_suggested_files, get_suggested_files, approve_suggested_files
)
from tools.file_tools import list_available_files, sample_file


def build_file_suggestion_agent(model_name: str = "openai/gpt-4o") -> Agent:
    llm = LiteLlm(model=model_name)

    instruction = """
    You are a constructive critic AI reviewing a list of files.
    Your goal is to suggest relevant files for constructing a knowledge graph.

    Task:
    Review the file list for relevance to the approved user goal.
    For any file you are unsure about, use 'sample_file' to inspect its content.
    Only consider structured data files (CSV, JSON) and unstructured markdown files.

    Prepare for the task:
    - use 'get_approved_user_goal' to understand the goal

    Think carefully, repeating these steps until finished:
    1. List available files using 'list_available_files'
    2. Evaluate each file's relevance; record suggestions using 'set_suggested_files'
    3. Use 'get_suggested_files' to confirm the list
    4. Ask the user to approve the suggested files
    5. If the user has feedback, go back to step 1 with that feedback in mind
    6. If approved, call 'approve_suggested_files' to finalise
    """

    return Agent(
        name="file_suggestion_agent_v1",
        model=llm,
        description="Analyzes available files and suggests which to use for graph construction.",
        instruction=instruction,
        tools=[
            get_approved_user_goal,
            list_available_files,
            sample_file,
            set_suggested_files,
            get_suggested_files,
            approve_suggested_files,
        ],
    )
