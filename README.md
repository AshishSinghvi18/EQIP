# EQIP — Engineering Quality Intelligence Platform

> Measures engineering quality across the full delivery chain. Traces defects to their true origin, scores each role on its own absolute facts, and provides interactive drill-down dashboards.

---

## Key Design Principles

| Principle | Description |
|-----------|-------------|
| **No shared point pool** | Each role is scored on its own absolute facts independently — no zero-sum competition |
| **Full-chain root cause** | Trace defects through Requirement → Dev → Code Review → Test → Automation → UAT → Release → Production |
| **AI suggests, humans decide** | Mandatory EM sign-off before any AI suggestion affects scores |
| **Immutable audit trail** | Every score change is append-only and replayable |
| **Explainable rankings** | Every rank and badge shows the facts behind it |
| **Diagnosis & coaching first** | Data's primary job is to show where quality breaks and coach the right person |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (React 18 + TypeScript + Vite)                     │
│  ─ Dashboard, drill-down charts, coaching, forecast views    │
│  ─ Recharts for data visualization                           │
├──────────────────────────────────────────────────────────────┤
│  Backend (FastAPI + Python 3.12)                             │
│  ─ REST API, scoring engine, AI services, import pipelines   │
│  ─ LLM integration (Qwen3/DeepSeek V4 via OpenAI API)       │
├──────────────────────────────────────────────────────────────┤
│  Database (PostgreSQL 16 + pgvector)                         │
│  ─ System of record, vector embeddings (BGE-M3), full-text   │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (with pgvector extension for semantic search)

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
pytest tests/ -v
# 74 tests covering all 4 phases
```

---

## Implemented Phases

### Phase 1 — Foundation ✅

Core platform capabilities for quality measurement and data capture.

| Feature | FR | Description |
|---------|-----|-------------|
| **Projects & Sprints** | FR-1 | Create and manage projects with sprint cycles |
| **Story Import** | FR-2 | Bulk import stories from Excel (.xlsx), CSV, and JSON files |
| **Bug Import** | FR-3 | Bulk import bugs from Excel (.xlsx), CSV, and JSON with auto-mapping |
| **Per-Role Scoring** | FR-4 | Independent scoring per role (Developer, BA, Tester, Automation) — no zero-sum |
| **Configurable Weights** | FR-5 | Admin-adjustable scoring weights per event type and role |
| **Immutable Event Log** | FR-11 | Append-only quality events — never overwritten, fully auditable |
| **Interactive Dashboard** | FR-12 | Executive summary, module heatmap, bug breakdown, root-cause drill-down |
| **Human Sign-off** | FR-9 | AI suggestions require EM approval before affecting any score |
| **Leaderboard** | FR-14 | Ranked leaderboard with supporting evidence for every position |
| **User & Team Mgmt** | — | Role-based users (Admin, EM, Developer, BA, Tester, Automation) and teams |
| **Story Attachments** | — | Upload reference documents (Word/PDF/Excel) to stories, max 50MB |

### Phase 2 — Intelligence ✅

AI-powered analysis and semantic understanding.

| Feature | FR | Description |
|---------|-----|-------------|
| **AI Root-Cause Suggestion** | FR-8 | LLM-powered (Qwen3/DeepSeek V4) root cause, owner, and severity suggestions with confidence scores; falls back to keyword-based rule engine |
| **EM Approval Workflow** | FR-9 | AI suggestions stored without affecting scores; EM explicitly approves to apply |
| **Semantic Search** | FR-10 | Hybrid search: pgvector cosine similarity (BGE-M3 embeddings) + keyword matching across stories, bugs, and events |
| **Similar Bug Finder** | FR-10 | "Find defects similar to BUG-X" using vector similarity |
| **Full-Chain RCA** | FR-6 | Traces defects through the complete delivery chain (Requirement → Dev → Code Review → Testing → Automation → UAT → Release → Production) |
| **Multi-Cause Ownership** | FR-6 | Supports shared/split ownership — not a single-villain model |
| **RCA Chain Summary** | FR-6 | Aggregated view showing where defects originate and which stages miss them |
| **Embedding Management** | — | Backfill embeddings, per-entity embedding generation, model tracking |
| **Dispute Handling** | FR-16 | Raise and resolve disputes against AI-assigned root cause/owner with full audit |

### Phase 3 — Insight ✅

Coaching, recognition, and trend analytics for continuous improvement.

| Feature | FR | Description |
|---------|-----|-------------|
| **Coaching Recommendations** | FR-15 | AI-generated coaching based on quality event patterns; dismissible per user |
| **Auto-Badge Evaluation** | FR-14 | Automatic badge awarding based on predefined quality criteria with evidence |
| **Badge System** | FR-14 | 7 badge types: Zero-Bug Champion, Edge-Case Hunter, Code Guardian, Automation Hero, Quality Champion, Security Sentinel, Requirement Master |
| **Quality Trend Lines** | §10.3 | Time-series quality metrics (bugs, positive/negative events) with configurable granularity (day/week/month) |
| **Bug Category Trends** | §10.3 | Bug root-cause category trends over time |
| **Severity Trends** | §10.3 | Bug severity distribution trends over time |
| **Module Risk View** | §10.3 | Composite risk score per module (0-100) based on bug density, severity, escaped defects, trend direction, unresolved backlog |
| **Score Progression** | — | User score trend over time per role and module |

### Phase 4 — Prediction ✅

Forecasting and organizational health intelligence.

| Feature | FR | Description |
|---------|-----|-------------|
| **Release-Risk Prediction** | — | Computes 0-100 risk score based on bug density, open severity, escaped defect rate, story completion, and historical patterns |
| **Risk Factor Breakdown** | — | Individual risk factors with impact weights and actionable recommendations |
| **Quality Trend Forecast** | — | Linear-regression-based prediction of next-period bug density, completion rate, and positive event ratio |
| **Engineering Health Index** | — | Single 0-100 composite score: zero-bug rate (40%) + positive event ratio (30%) + production stability (30%) |
| **Org Benchmarking** | — | Cross-project quality comparison with ranked health scores and org-wide averages |

---

## Frontend Pages

| Page | Features |
|------|----------|
| **Dashboard** | Executive summary cards, severity breakdown, module heatmap, root-cause charts |
| **Stories** | Story list, onboarding/import wizard, detail view |
| **Bugs** | Bug list, import, AI suggestion triggers, approval workflow |
| **Scores** | Per-user role scores with event breakdown |
| **Leaderboard** | Ranked quality leaders with evidence drill-down |
| **Search** | Semantic + keyword search across all entities |
| **Coaching** | Personalized recommendations, health index display, forecast summaries |
| **Trends** | Quality trend charts, module risk heatmap, category/severity trend lines |
| **Forecast** | Release-risk gauge, risk factor waterfall, trend predictions |

---

## API Endpoints

### Core (Phase 1)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users` | GET/POST | User management |
| `/api/teams` | GET/POST | Team management |
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
| `/api/attachments/stories/{id}/attachments` | POST/GET | Upload/list story reference documents |

### Dashboard (Phase 1)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/summary` | GET | Executive quality summary |
| `/api/dashboard/module-heatmap` | GET | Module defect density |
| `/api/dashboard/bug-type-breakdown` | GET | Bug category breakdown |
| `/api/dashboard/root-cause-breakdown` | GET | Root cause drill-down |
| `/api/dashboard/leaderboard` | GET | Ranked leaderboard with facts |

### Intelligence (Phase 2)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bugs/{id}/ai-suggest` | POST | AI root-cause/owner/severity suggestion |
| `/api/bugs/{id}/approve-suggestion` | POST | EM approves AI suggestion |
| `/api/search` | GET | Hybrid semantic + keyword search |
| `/api/search/similar/{bug_id}` | GET | Find similar bugs via vector similarity |
| `/api/rca/analyze/{bug_id}` | POST | Perform full-chain RCA |
| `/api/rca/{bug_id}` | GET | Get existing chain analysis |
| `/api/rca/{analysis_id}/approve` | POST | EM approves chain analysis |
| `/api/rca/summary/chain` | GET | Aggregated chain analysis summary |
| `/api/embeddings/backfill` | POST | Backfill all vector embeddings |
| `/api/embeddings/story/{id}` | POST | Generate embedding for a story |
| `/api/embeddings/bug/{id}` | POST | Generate embedding for a bug |
| `/api/disputes` | GET/POST | List/create disputes |
| `/api/disputes/{id}/resolve` | POST | Resolve a dispute |

### Insight (Phase 3)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/coaching/{user_id}` | GET | Get coaching recommendations |
| `/api/coaching/{user_id}/generate` | POST | Generate new coaching recommendations |
| `/api/coaching/{id}/dismiss` | POST | Dismiss a recommendation |
| `/api/badges` | GET/POST | List/create badge types |
| `/api/badges/user/{user_id}` | GET | Get user's badges with evidence |
| `/api/badges/award` | POST | Award badge to user |
| `/api/trends/quality-over-time` | GET | Quality trend lines (day/week/month) |
| `/api/trends/bug-category-trend` | GET | Bug category trends |
| `/api/trends/severity-trend` | GET | Severity distribution trends |
| `/api/trends/module-risk` | GET | Module risk assessment view |
| `/api/trends/badges/evaluate/{user_id}` | POST | Auto-evaluate and award badges |
| `/api/trends/score-trend/{user_id}` | GET | User score progression |

### Prediction (Phase 4)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/prediction/forecast` | POST | Generate release-risk prediction |
| `/api/prediction/forecast/{project_id}` | GET | Get recent forecasts |
| `/api/prediction/trend/{project_id}` | GET | Quality trend with forecast |
| `/api/prediction/health/{project_id}` | GET | Engineering Health Index |
| `/api/prediction/benchmarking` | GET | Org-level cross-project comparison |
| `/api/forecast` | POST | Generate forecast (alternate) |
| `/api/forecast/{project_id}` | GET | Get forecasts (alternate) |
| `/api/health/{project_id}` | GET | Health index (alternate) |

---

## Scoring Model

Each role has independent fact-based scoring. No shared pool — two people on the same story can both score well.

| Role | Gains (positive events) | Losses (negative events) |
|------|------------------------|--------------------------|
| **Developer** | First-time-right code review, zero-defect story, reusable component, performance/security improvement, early completion | Validation bug, logic bug, high-severity defect, production defect, rework cycle, failed code review |
| **BA** | Complete acceptance criteria, well-documented story, edge cases covered, low clarification count | Requirement gap, wrong flow, missing acceptance criteria, late requirement changes |
| **Tester** | Critical/edge/boundary/security/performance issues found before release, strong regression coverage | Escaped production defect, weak regression, false positive, incomplete/late testing |
| **Automation** | Regression automated, stable scripts, high coverage, fast execution, CI integration | Broken scripts, flaky tests, low coverage, maintenance backlog |

---

## Badge System

| Badge | Criteria | Evidence |
|-------|----------|----------|
| 🏆 Zero-Bug Champion | ≥3 zero-defect stories in a period | Story IDs with zero defects |
| 🔍 Edge-Case Hunter | ≥3 edge/boundary issues found | Count of edge cases caught |
| 🛡️ Code Guardian | ≥5 first-time-right code reviews | Number of clean review passes |
| 🤖 Automation Hero | ≥4 automation quality events | Automation contribution count |
| ⭐ Quality Champion | ≥10 positive events AND positive > 2× negative | Positive/negative ratio |
| 🔒 Security Sentinel | ≥2 security issues found/improved | Security contribution count |
| 📋 Requirement Master | ≥5 requirement quality events | Quality requirement event count |

---

## Test Coverage

```
tests/test_core.py    — Phase 1: Scoring engine, event recording, weight system
tests/test_phase2.py  — Phase 2: AI suggestions, semantic search, embeddings, chain RCA
tests/test_phase3.py  — Phase 3: Module risk, trend analytics, auto-badge evaluation
tests/test_phase4.py  — Phase 4: Forecast, health index, org benchmarking, trend prediction

Total: 74 tests — all passing ✅
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Recharts |
| Backend | FastAPI, SQLAlchemy, Pydantic v2 |
| Database | PostgreSQL 16, pgvector |
| AI/ML | OpenAI-compatible API (Qwen3/DeepSeek V4), BGE-M3 embeddings |
| Testing | pytest, pytest-asyncio |
| Deployment | Docker, Docker Compose |

---

## License

Internal project — Engineering Quality Intelligence Platform.