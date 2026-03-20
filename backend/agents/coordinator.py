"""
Pipeline coordinator — orchestrates the full multi-agent pipeline
and provides a stateful session interface used by the WebSocket router.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator

from agents.base import AgentCaller, make_agent_caller
from agents.user_intent import build_user_intent_agent
from agents.file_suggestion import build_file_suggestion_agent
from agents.schema_proposal import build_schema_refinement_loop
from agents.schema_unstructured import build_ner_agent, build_fact_extraction_agent
from agents.kg_construction import construct_domain_graph, build_subject_graph
from config import get_settings


class PipelineStage(str, Enum):
    IDLE = "idle"
    USER_INTENT = "user_intent"
    FILE_SUGGESTION = "file_suggestion"
    SCHEMA_PROPOSAL = "schema_proposal"
    NER = "ner"
    FACT_EXTRACTION = "fact_extraction"
    KG_CONSTRUCTION = "kg_construction"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class PipelineState:
    stage: PipelineStage = PipelineStage.IDLE
    session_state: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class AgentCoordinator:
    """
    Top-level coordinator that manages a conversational pipeline session.
    Each HTTP session maps to one coordinator instance.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = PipelineState()
        self._caller: AgentCaller | None = None
        cfg = get_settings()
        self._model = f"openai/{cfg.openai_model}"

    # ── Stage transitions ──────────────────────────────────

    def _stage_order(self) -> list[PipelineStage]:
        return [
            PipelineStage.USER_INTENT,
            PipelineStage.FILE_SUGGESTION,
            PipelineStage.SCHEMA_PROPOSAL,
            PipelineStage.NER,
            PipelineStage.FACT_EXTRACTION,
            PipelineStage.KG_CONSTRUCTION,
        ]

    def advance_stage(self) -> None:
        order = self._stage_order()
        try:
            idx = order.index(self.state.stage)
            self.state.stage = order[idx + 1]
        except (ValueError, IndexError):
            self.state.stage = PipelineStage.COMPLETE

    # ── Chat entry point ───────────────────────────────────

    async def chat(self, user_message: str) -> AsyncGenerator[str, None]:
        """Route the user message to the active stage agent and stream back tokens."""
        stage = self.state.stage

        if stage == PipelineStage.IDLE:
            self.state.stage = PipelineStage.USER_INTENT
            stage = PipelineStage.USER_INTENT

        try:
            if stage == PipelineStage.USER_INTENT:
                async for token in self._chat_user_intent(user_message):
                    yield token

            elif stage == PipelineStage.FILE_SUGGESTION:
                async for token in self._chat_file_suggestion(user_message):
                    yield token

            elif stage == PipelineStage.SCHEMA_PROPOSAL:
                async for token in self._chat_schema_proposal(user_message):
                    yield token

            elif stage == PipelineStage.NER:
                async for token in self._chat_ner(user_message):
                    yield token

            elif stage == PipelineStage.FACT_EXTRACTION:
                async for token in self._chat_fact_extraction(user_message):
                    yield token

            elif stage == PipelineStage.KG_CONSTRUCTION:
                async for token in self._run_kg_construction():
                    yield token

            elif stage == PipelineStage.COMPLETE:
                yield "✅ Pipeline complete! The knowledge graph has been built."

        except Exception as exc:  # pylint: disable=broad-except
            self.state.stage = PipelineStage.ERROR
            self.state.error = str(exc)
            yield f"❌ Error: {exc}"

    # ── Stage-specific helpers ─────────────────────────────

    async def _chat_user_intent(self, msg: str) -> AsyncGenerator[str, None]:
        if self._caller is None or getattr(self._caller.agent, "name", "") != "user_intent_agent_v1":
            agent = build_user_intent_agent(self._model)
            self._caller = await make_agent_caller(agent, self.state.session_state)

        async for token in self._caller.stream(msg):
            yield token

        session = await self._caller.get_session()
        self.state.session_state.update(session.state)

        if "approved_user_goal" in self.state.session_state:
            self.state.stage = PipelineStage.FILE_SUGGESTION
            yield "\n\n---\n✅ **Goal approved!** Let's now select data files.\n"
            self._caller = None

    async def _chat_file_suggestion(self, msg: str) -> AsyncGenerator[str, None]:
        if self._caller is None or getattr(self._caller.agent, "name", "") != "file_suggestion_agent_v1":
            agent = build_file_suggestion_agent(self._model)
            self._caller = await make_agent_caller(agent, self.state.session_state)

        async for token in self._caller.stream(msg):
            yield token

        session = await self._caller.get_session()
        self.state.session_state.update(session.state)

        if "approved_files" in self.state.session_state:
            self.state.stage = PipelineStage.SCHEMA_PROPOSAL
            yield "\n\n---\n✅ **Files approved!** Now proposing a graph schema.\n"
            self._caller = None

    async def _chat_schema_proposal(self, msg: str) -> AsyncGenerator[str, None]:
        if self._caller is None:
            agent = build_schema_refinement_loop(self._model)
            self._caller = await make_agent_caller(agent, {
                **self.state.session_state,
                "feedback": "",
            })

        async for token in self._caller.stream(msg):
            yield token

        session = await self._caller.get_session()
        self.state.session_state.update(session.state)

        if "approved_construction_plan" in self.state.session_state:
            self.state.stage = PipelineStage.NER
            yield "\n\n---\n✅ **Schema approved!** Let's identify entity types in the text.\n"
            self._caller = None

    async def _chat_ner(self, msg: str) -> AsyncGenerator[str, None]:
        if self._caller is None:
            agent = build_ner_agent(self._model)
            self._caller = await make_agent_caller(agent, self.state.session_state)

        async for token in self._caller.stream(msg):
            yield token

        session = await self._caller.get_session()
        self.state.session_state.update(session.state)

        if "approved_entity_types" in self.state.session_state:
            self.state.stage = PipelineStage.FACT_EXTRACTION
            yield "\n\n---\n✅ **Entities approved!** Now extracting fact types.\n"
            self._caller = None

    async def _chat_fact_extraction(self, msg: str) -> AsyncGenerator[str, None]:
        if self._caller is None:
            agent = build_fact_extraction_agent(self._model)
            self._caller = await make_agent_caller(agent, self.state.session_state)

        async for token in self._caller.stream(msg):
            yield token

        session = await self._caller.get_session()
        self.state.session_state.update(session.state)

        if "approved_fact_types" in self.state.session_state:
            self.state.stage = PipelineStage.KG_CONSTRUCTION
            yield "\n\n---\n✅ **Fact types approved!** Building the knowledge graph now...\n"
            self._caller = None

    async def _run_kg_construction(self) -> AsyncGenerator[str, None]:
        yield "⚙️ Constructing domain graph from CSV files...\n"
        plan = self.state.session_state.get("approved_construction_plan", {})
        result = construct_domain_graph(plan)
        if result["status"] == "error":
            yield f"❌ Domain graph error: {result['error_message']}\n"
        else:
            yield "✅ Domain graph built.\n"

        files = self.state.session_state.get("approved_files", [])
        entities = self.state.session_state.get("approved_entity_types", [])
        facts = self.state.session_state.get("approved_fact_types", {})

        md_files = [f for f in files if f.endswith(".md")]
        if md_files:
            yield "⚙️ Building subject/lexical graph from markdown files...\n"
            result = await build_subject_graph(md_files, entities, facts)
            if result["status"] == "error":
                yield f"⚠️ Subject graph: {result['error_message']}\n"
            else:
                yield f"✅ Subject graph built ({len(result['subject_graph_built']['files_processed'])} files).\n"

        self.state.stage = PipelineStage.COMPLETE
        yield "\n🎉 **Knowledge graph fully constructed!** Explore it in the Graph View.\n"
