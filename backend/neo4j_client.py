"""
Neo4j client wrapper — productionized from neo4j_for_adk.py course helper.
Provides a clean interface for sending Cypher queries and standard tool response helpers.
"""
from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase, exceptions as neo4j_exc

from config import get_settings


def tool_success(key: str, value: Any) -> dict:
    """Standard success response for ADK tools."""
    return {"status": "success", key: value}


def tool_error(message: str) -> dict:
    """Standard error response for ADK tools."""
    return {"status": "error", "error_message": message}


class GraphDB:
    """Thin wrapper around the Neo4j Python driver."""

    def __init__(self) -> None:
        self._driver = None

    def _ensure_connected(self) -> None:
        if self._driver is None:
            cfg = get_settings()
            self._driver = GraphDatabase.driver(
                cfg.neo4j_uri,
                auth=(cfg.neo4j_username, cfg.neo4j_password),
            )

    def get_driver(self):
        self._ensure_connected()
        return self._driver

    def send_query(self, query: str, params: dict | None = None) -> dict:
        """Execute a Cypher query and return a standardised result dict."""
        self._ensure_connected()
        try:
            with self._driver.session() as session:
                result = session.run(query, params or {})
                records = [dict(r) for r in result]
                return tool_success("query_result", records)
        except neo4j_exc.ServiceUnavailable as exc:
            return tool_error(f"Neo4j unavailable: {exc}")
        except Exception as exc:  # pylint: disable=broad-except
            return tool_error(str(exc))

    def is_connected(self) -> bool:
        """Return True if the database is reachable."""
        try:
            result = self.send_query("RETURN 1 AS ok")
            return result["status"] == "success"
        except Exception:  # pylint: disable=broad-except
            return False

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None


# Singleton instance used throughout the app
graphdb = GraphDB()
