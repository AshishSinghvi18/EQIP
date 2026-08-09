"""EQIP - Engineering Quality Intelligence Platform API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import attachments, dashboard, intelligence, prediction, projects, quality, stories, story_quality, trends, users

app = FastAPI(
    title="EQIP - Engineering Quality Intelligence Platform",
    description=(
        "Measures engineering quality across the full delivery chain. "
        "Traces defects to their true origin, scores each role on its own facts, "
        "and provides interactive drill-down dashboards. "
        "Implements all 4 phases: Foundation, Intelligence, Insight, and Prediction."
    ),
    version="2.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(users.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(stories.router, prefix="/api")
app.include_router(quality.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(attachments.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")
app.include_router(story_quality.router, prefix="/api")
app.include_router(prediction.router, prefix="/api")
app.include_router(trends.router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "EQIP",
        "version": "2.0.0",
        "description": "Engineering Quality Intelligence Platform",
        "phases": {
            "phase_1": "Foundation - Projects, stories, bugs, scoring, audit trail, dashboards",
            "phase_2": "Intelligence - AI RCA suggestions, semantic search, full-chain RCA",
            "phase_3": "Insight - Coaching, badges, leaderboards, trend analytics",
            "phase_4": "Prediction - Release risk, quality forecast, health index",
        },
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
