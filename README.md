# EQIP — Engineering Quality Intelligence Platform

> Measures engineering quality across the full delivery chain. Traces defects to their true origin, scores each role on its own absolute facts, and provides interactive drill-down dashboards.

## Key Design Principles

- **No shared point pool** — each role scored on its own facts independently
- **Full-chain root cause** — trace defects through Requirement → Dev → Test → Production
- **AI suggests, humans decide** — mandatory EM sign-off before scores are affected
- **Immutable audit trail** — every score change is append-only and replayable
- **Explainable rankings** — every rank/badge shows the facts behind it

## Architecture

```
Frontend (React + TypeScript)     →  Dashboard, drill-down, charts
Backend  (FastAPI + Python)       →  REST API, scoring engine, import
Database (PostgreSQL + pgvector)  →  System of record, embeddings
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set DATABASE_URL in .env or environment
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose (full stack)

```bash
docker-compose up
```

### Run Tests

```bash
cd backend
pytest tests/
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects` | GET/POST | Project management |
| `/api/projects/{id}/sprints` | GET/POST | Sprint management |
| `/api/stories` | GET/POST | Story CRUD |
| `/api/stories/import` | POST | Import stories from Excel/CSV/JSON |
| `/api/bugs` | GET/POST | Bug CRUD |
| `/api/bugs/import` | POST | Import bugs from Excel/CSV/JSON |
| `/api/events` | GET/POST | Quality events (immutable audit trail) |
| `/api/events/{id}/approve` | POST | EM approval of AI suggestions |
| `/api/scores/{actor_id}` | GET | Get role scores |
| `/api/scores/compute` | POST | Recompute scores from events |
| `/api/weights` | GET/POST | Configurable scoring weights |
| `/api/dashboard/summary` | GET | Executive quality summary |
| `/api/dashboard/module-heatmap` | GET | Module defect density |
| `/api/dashboard/bug-type-breakdown` | GET | Bug category breakdown |
| `/api/dashboard/root-cause-breakdown` | GET | Root cause drill-down |
| `/api/dashboard/leaderboard` | GET | Ranked leaderboard with facts |

## Phase 1 (Foundation) — Implemented

- ✅ Projects & sprints management (FR-1)
- ✅ Story import from Excel/CSV/JSON (FR-2)
- ✅ Bug import from Excel/CSV/JSON (FR-3)
- ✅ Per-role scoring — independent, no zero-sum (FR-4)
- ✅ Configurable weights (FR-5)
- ✅ Immutable quality event log (FR-11)
- ✅ Interactive dashboard with drill-down (FR-12)
- ✅ Mandatory human sign-off for AI events (FR-9)
- ✅ Leaderboard with evidence (FR-14)

## Roadmap

- **Phase 2**: AI root-cause suggestions, semantic search (pgvector), full-chain RCA
- **Phase 3**: Coaching recommendations, badges, trend analytics
- **Phase 4**: Release-risk prediction, quality forecasting