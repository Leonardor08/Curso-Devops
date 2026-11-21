"""FastAPI application entry point."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import tasks


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create the entities when the server starts (not at import time).

    Creating them on startup instead of on import keeps the test suite from
    generating an empty ``tasks.db`` file just by importing ``app.main``.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="DevOps Task Manager API",
    description="API REST de gestión de tareas — Proyecto Integrador DevOps",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(tasks.router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Endpoint de salud usado por liveness y readiness probes de Kubernetes."""
    return {"status": "ok"}
