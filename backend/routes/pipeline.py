"""
Pipeline status and file management routes.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from config import get_settings
from neo4j_client import graphdb

router = APIRouter(prefix="/api", tags=["pipeline", "files"])


@router.get("/files")
async def list_files():
    """List all data files available for import."""
    data_dir = Path(get_settings().data_dir)
    if not data_dir.exists():
        return {"files": [], "error": f"Data directory not found: {data_dir}"}
    files = [
        {
            "path": str(f.relative_to(data_dir)),
            "name": f.name,
            "size_bytes": f.stat().st_size,
            "type": "csv" if f.suffix == ".csv" else "markdown" if f.suffix == ".md" else "other",
        }
        for f in data_dir.rglob("*")
        if f.is_file()
    ]
    return {"files": files}


@router.get("/health")
async def health():
    """Overall system health check."""
    neo4j_ok = graphdb.is_connected()
    return {
        "status": "ok" if neo4j_ok else "degraded",
        "neo4j": "connected" if neo4j_ok else "unavailable",
    }
