"""
FastAPI application entry point.
Run:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from neo4j_client import graphdb
from routes.chat import router as chat_router
from routes.graph import router as graph_router
from routes.pipeline import router as pipeline_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Agentic RAG — Knowledge Graph API starting up...")
    print(f"   Neo4j: {get_settings().neo4j_uri}")
    yield
    # Shutdown
    graphdb.close()
    print("👋 Shutting down — Neo4j connection closed.")


def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(
        title="Agentic RAG — Knowledge Graph API",
        description=(
            "A multi-agent system that constructs knowledge graphs from structured and "
            "unstructured data using Google ADK agents and Neo4j."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router)
    app.include_router(graph_router)
    app.include_router(pipeline_router)

    @app.get("/", tags=["root"])
    async def root():
        return {
            "name": cfg.app_name,
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
