"""
Agent Runner base class — extracted from helper.py (intro_to_adk notebooks).
Provides AgentCaller and make_agent_caller factory.
"""
from __future__ import annotations

from typing import Any, AsyncGenerator, Optional

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types


class AgentCaller:
    """Convenience wrapper for interacting with a single ADK agent in a single session."""

    def __init__(self, agent: Agent, runner: Runner, user_id: str, session_id: str):
        self.agent = agent
        self.runner = runner
        self.user_id = user_id
        self.session_id = session_id

    async def get_session(self):
        return await self.runner.session_service.get_session(
            app_name=self.runner.app_name,
            user_id=self.user_id,
            session_id=self.session_id,
        )

    async def call(self, user_message: str, verbose: bool = False) -> str:
        """Send a message to the agent and return the final text response."""
        content = types.Content(role="user", parts=[types.Part(text=user_message)])
        final_response = "Agent did not produce a final response."

        async for event in self.runner.run_async(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=content,
        ):
            if verbose:
                print(f"  [Event] {event.author}: {event.content}")
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response = f"Agent escalated: {event.error_message or 'No detail'}"
                break

        return final_response

    async def stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """Yield agent events as SSE-friendly strings for WebSocket streaming."""
        content = types.Content(role="user", parts=[types.Part(text=user_message)])
        async for event in self.runner.run_async(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        yield part.text
            if event.is_final_response():
                break


async def make_agent_caller(
    agent: Agent,
    initial_state: Optional[dict[str, Any]] = None,
) -> AgentCaller:
    """Factory: create an AgentCaller with its own session."""
    app_name = f"{agent.name}_app"
    user_id = f"{agent.name}_user"
    session_id = f"{agent.name}_session_01"

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state or {},
    )

    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    return AgentCaller(agent, runner, user_id, session_id)
