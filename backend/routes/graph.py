"""
Graph query and visualization endpoints.
Returns Neo4j data formatted for the frontend graph renderer.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from neo4j_client import graphdb

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/health")
async def graph_health():
    """Check Neo4j connectivity."""
    connected = graphdb.is_connected()
    return {"connected": connected}


@router.get("/stats")
async def graph_stats():
    """Overall graph statistics."""
    result = graphdb.send_query("""
        CALL {
            MATCH (n) RETURN count(n) AS nodes
        }
        CALL {
            MATCH ()-[r]->() RETURN count(r) AS relationships
        }
        CALL {
            MATCH (n) RETURN collect(DISTINCT labels(n)) AS label_groups
        }
        RETURN nodes, relationships, label_groups
    """)
    if result["status"] == "error":
        return {"error": result["error_message"]}
    row = result["query_result"][0] if result["query_result"] else {}
    return {
        "nodes": row.get("nodes", 0),
        "relationships": row.get("relationships", 0),
        "label_groups": row.get("label_groups", []),
    }


@router.get("/visualize")
async def visualize(
    limit: int = Query(default=200, ge=1, le=1000),
    label: str | None = Query(default=None),
):
    """
    Returns nodes and edges formatted for vis-network / force-graph library.
    """
    if label:
        cypher = f"""
            MATCH (n:`{label}`)-[r]->(m)
            RETURN n, r, m
            LIMIT $limit
        """
    else:
        cypher = """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT $limit
        """

    result = graphdb.send_query(cypher, {"limit": limit})
    if result["status"] == "error":
        return {"nodes": [], "edges": [], "error": result["error_message"]}

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for row in result["query_result"]:
        n = row.get("n", {})
        m = row.get("m", {})
        r = row.get("r", {})

        if n:
            nid = str(n.get("element_id", n.get("id", id(n))))
            if nid not in nodes:
                nodes[nid] = {
                    "id": nid,
                    "label": list(n.get("labels", ["Node"]))[0] if n.get("labels") else "Node",
                    "properties": dict(n),
                    "title": _node_title(n),
                }
        if m:
            mid = str(m.get("element_id", m.get("id", id(m))))
            if mid not in nodes:
                nodes[mid] = {
                    "id": mid,
                    "label": list(m.get("labels", ["Node"]))[0] if m.get("labels") else "Node",
                    "properties": dict(m),
                    "title": _node_title(m),
                }
        if r and n and m:
            nid = str(n.get("element_id", n.get("id", id(n))))
            mid = str(m.get("element_id", m.get("id", id(m))))
            edges.append({
                "from": nid,
                "to": mid,
                "label": r.get("type", ""),
                "properties": dict(r),
            })

    return {"nodes": list(nodes.values()), "edges": edges}


@router.get("/labels")
async def get_labels():
    """Returns all distinct node labels in the graph."""
    result = graphdb.send_query("CALL db.labels() YIELD label RETURN collect(label) AS labels")
    if result["status"] == "error":
        return {"labels": []}
    row = result["query_result"][0] if result["query_result"] else {}
    return {"labels": row.get("labels", [])}


@router.post("/query")
async def run_cypher(body: dict):
    """Execute a custom read-only Cypher query (for power users)."""
    cypher = body.get("query", "")
    if not cypher.strip():
        return {"error": "Empty query"}
    # Basic safety: only allow read queries
    forbidden = ("CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DROP", "CALL {")
    upper = cypher.upper()
    if any(kw in upper for kw in forbidden):
        return {"error": "Only read-only Cypher queries are allowed via this endpoint."}
    return graphdb.send_query(cypher)


def _node_title(node: dict) -> str:
    """Pick a display-friendly property value for a node tooltip."""
    for key in ("name", "product_name", "assembly_name", "part_name", "title", "id"):
        val = node.get("properties", node).get(key)
        if val:
            return str(val)
    return "Node"
