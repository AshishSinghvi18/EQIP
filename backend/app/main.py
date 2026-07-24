from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.routes.bugs import router as bugs_router
from app.routes.dashboard import router as dashboard_router
from app.routes.projects import router as projects_router
from app.routes.scoring import router as scoring_router
from app.routes.stories import router as stories_router
from app.services.seed_data import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed_demo_data(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Engineering Quality Intelligence Platform backend API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, prefix=settings.api_prefix)
app.include_router(stories_router, prefix=settings.api_prefix)
app.include_router(bugs_router, prefix=settings.api_prefix)
app.include_router(scoring_router, prefix=settings.api_prefix)
app.include_router(projects_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}
