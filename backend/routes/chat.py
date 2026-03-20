"""
WebSocket + REST chat route.
Each browser tab gets its own AgentCoordinator via session_id.
"""
from __future__ import annotations

import json
import uuid
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agents.coordinator import AgentCoordinator

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory coordinator registry (per session)
_coordinators: Dict[str, AgentCoordinator] = {}


def _get_or_create(session_id: str) -> AgentCoordinator:
    if session_id not in _coordinators:
        _coordinators[session_id] = AgentCoordinator(session_id)
    return _coordinators[session_id]


@router.websocket("/ws/{session_id}")
async def chat_ws(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time agent chat.
    Client sends: {"message": "..."}
    Server streams: {"type": "token"|"status"|"error", "data": "..."}
    """
    await websocket.accept()
    coordinator = _get_or_create(session_id)

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            user_message = payload.get("message", "")

            if not user_message.strip():
                continue

            # Echo the user message type confirmation
            await websocket.send_json({
                "type": "status",
                "data": coordinator.state.stage.value,
            })

            async for token in coordinator.chat(user_message):
                await websocket.send_json({"type": "token", "data": token})

            # Send final stage after response
            await websocket.send_json({
                "type": "status",
                "data": coordinator.state.stage.value,
            })
            await websocket.send_json({"type": "done", "data": ""})

    except WebSocketDisconnect:
        pass
    except Exception as exc:  # pylint: disable=broad-except
        await websocket.send_json({"type": "error", "data": str(exc)})


@router.get("/new-session")
async def new_session():
    """Creates a new pipeline session and returns its ID."""
    sid = str(uuid.uuid4())
    _coordinators[sid] = AgentCoordinator(sid)
    return {"session_id": sid}


@router.get("/status/{session_id}")
async def session_status(session_id: str):
    """Returns the current pipeline stage and session state for a session."""
    coord = _coordinators.get(session_id)
    if not coord:
        return {"error": "Session not found"}
    return {
        "session_id": session_id,
        "stage": coord.state.stage.value,
        "error": coord.state.error,
        "state_keys": list(coord.state.session_state.keys()),
    }
