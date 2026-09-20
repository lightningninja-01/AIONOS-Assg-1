"""
FastAPI application factory for the Executive Productivity Agent.

On startup:
  1. Runs the full commitment pipeline (load → extract → deduplicate → resolve)
  2. Builds the LangGraph Q&A graph
  3. Makes both available on app.state for all request handlers

Adapted from the Omni-Channel project's main.py lifespan pattern.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import build_qa_graph
from app.agent.llm_service import LLMService
from app.config.settings import get_settings
from app.engine.commitment_store import CommitmentStore
from app.routers import brief, query
from app.utils.logger import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings

    log.info(f"Starting {settings.app_name}...")
    log.info(f"Simulated today: {settings.simulated_today}")
    log.info(f"LLM model: {settings.groq_model}")

    # Run the full commitment extraction pipeline
    store = CommitmentStore()
    await store.build()
    app.state.commitment_store = store

    # Build and compile the LangGraph Q&A graph
    llm = LLMService()
    qa_graph = build_qa_graph(store, llm)
    app.state.qa_graph = qa_graph

    log.info("Application ready.")
    yield
    log.info("Application shutdown.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Executive Productivity Agent — AIONOS Assignment 1",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(brief.router, prefix="/api", tags=["brief"])
    app.include_router(query.router, prefix="/api", tags=["query"])

    @app.get("/")
    async def root():
        return {"app": settings.app_name, "status": "ok", "simulated_today": settings.simulated_today}

    @app.get("/health")
    async def health():
        store = app.state.commitment_store
        return {
            "status": "ok",
            "commitments_loaded": len(store.all()),
            "simulated_today": settings.simulated_today,
            "model": settings.groq_model,
        }

    @app.get("/api/commitments")
    async def list_commitments():
        """Debug endpoint — list all commitments in the store."""
        store = app.state.commitment_store
        return {"commitments": store.all()}

    return app


app = create_app()
