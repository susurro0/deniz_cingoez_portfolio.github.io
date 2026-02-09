from __future__ import annotations

from time import time
from automation_app.models.workflow_state import WorkflowState
from typing import Dict


class StateStore:
    """
        In-memory implementation of the Agentic State Store.

        ARCHITECTURAL NOTE: This is a thread-safe dictionary implementation for POC purposes.
        In a production environment, this would be replaced by a persistent, distributed
        store such as Redis or CosmosDB to support horizontal scaling and session
        persistence across container restarts.
    """

    def __init__(self):
        # session_id -> context
        self.storage: Dict[str, dict] = {}

    async def save_context(
        self,
        session_id: str,
        data: dict,
        state: WorkflowState = WorkflowState.PROPOSED,
        timestamp: float | None = None,
    ):
        self.storage[session_id] = {
            "state": state,
            "data": data,
            "timestamp": timestamp or time(),
        }

    async def get_context(self, session_id: str) -> dict:
        return self.storage.get(
            session_id,
            {
                "state": WorkflowState.PROPOSED,
                "data": {},
                "timestamp": time(),
            },
        )

    async def get_all_sessions(self) -> Dict[str, dict]:
        """
        Returns all sessions for cleanup / inspection.
        """
        return self.storage

    async def delete_session(self, session_id: str):
        """
        Remove a session (used by HITL cleanup).
        """
        self.storage.pop(session_id, None)
