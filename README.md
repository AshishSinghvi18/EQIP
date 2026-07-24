# EQIP — Engineering Quality Intelligence Platform

A production-grade platform that measures engineering quality across the full delivery chain, traces defects to their true origin, and provides actionable coaching through interactive dashboards.

![Dashboard](https://img.shields.io/badge/Dashboard-React%20%2B%20TypeScript-blue)
![API](https://img.shields.io/badge/API-FastAPI%20%2B%20Python-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 What EQIP Does

- **Measures quality, not activity** — tracks defects, root causes, and prevention across roles
- **Per-role absolute scoring** — each role (Developer, BA, Tester, Automation) scored on its own facts, never zero-sum
- **Full-chain root cause analysis** — traces defects through Requirement → Development → Code Review → Testing → Production
- **Interactive drill-down dashboards** — click from module heatmap → bug type → root cause → specific stories
- **AI-powered suggestions** — proposes root cause, owner, severity with confidence scores (human sign-off required)
- **Fact-based recognition** — leaderboards and badges always show evidence, not bare numbers

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           React SPA (TypeScript + Tailwind)      │
│     Glass-morphism Dashboard • Recharts • RQ     │
└─────────────────────┬───────────────────────────┘
                      │ REST / JSON
┌─────────────────────┴───────────────────────────┐
│              FastAPI Backend (Python)             │
│  Scoring Engine • Event Store • Dashboard APIs   │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────┐
│        PostgreSQL + pgvector (Production)         │
│        SQLite (Development)                       │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm 9+

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API starts at `http://localhost:8000` with seed data auto-loaded.

### Frontend

```bash
cd frontend
npm install
npm start
```

The dashboard opens at `http://localhost:3000`.

### Docker (Production)

```bash
docker-compose up --build
```

Access the application at `http://localhost`.

---

## 📊 Dashboard Features

### Executive Quality Dashboard
- **Quality Index cards** — Sprint Quality, Escaped Defect %, Release Quality, Automation Coverage
- **Module Heatmap** — color-coded quality by module (green → red)
- **Trend Charts** — quality over time per module/team
- **Chain View** — where in the delivery chain defects originate

### Drill-Down Flow
```
Module Heatmap (Auth is red)
   ↓ click
Bug-type breakdown: Validation 41% · UI 22% · API 12%
   ↓ click "Validation"
Root-cause breakdown: Requirement gap 55% · Dev skipped 30%
   ↓ click "Requirement gap"
List of exact stories + RCA notes + who/what/when
```

### Role Dashboards
Each role sees their own facts, trends, and coaching tips.

### Leaderboard & Recognition
Fact-based rankings: "Rank #1 — 4 critical bugs caught pre-release, 0 escaped defects across 9 stories"

---

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/dashboard/overview` | Quality index KPI cards |
| `GET /api/dashboard/module-heatmap` | Module quality for heatmap |
| `GET /api/dashboard/bug-breakdown?module=Auth` | Bug type breakdown by module |
| `GET /api/dashboard/root-cause-breakdown?module=Auth&category=Validation` | RCA drill-down |
| `GET /api/dashboard/trend` | Quality trend over time |
| `GET /api/dashboard/leaderboard` | Top performers by role |
| `GET /api/dashboard/chain-view` | Defect origin by chain stage |
| `GET /api/stories` | List stories |
| `GET /api/bugs` | List bugs |
| `GET /api/projects` | List projects |
| `GET /api/scoring/role-scores` | Per-role score breakdown |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Recharts, React Query |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | SQLite (dev) / PostgreSQL + pgvector (prod) |
| Deployment | Docker, Nginx |
| Design | Dark theme, glass-morphism, Inter font |

---

## 📁 Project Structure

```
EQIP/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, database setup
│   │   ├── models/        # SQLAlchemy + Pydantic schemas
│   │   ├── routes/        # API endpoints
│   │   └── services/      # Scoring engine, seed data
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/           # API client + React Query hooks
│   │   ├── components/    # Dashboard, layout, common components
│   │   ├── pages/         # Route pages
│   │   └── types/         # TypeScript interfaces
│   ├── tailwind.config.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── EQIP-Design-Spec.md
```

---

## 🔒 Design Principles

1. **No shared point pie** — each role scored on its own absolute facts
2. **AI suggests, humans decide** — EM sign-off required before scores affected
3. **Full-chain root cause** — traces defects to true origin, supports shared ownership
4. **Every number is a doorway** — all metrics drill down to specific stories
5. **Coaching first** — data drives improvement, not punishment

---

## 📋 Roadmap

- [x] **Phase 1** — Foundation: Models, scoring, import, basic dashboards
- [ ] **Phase 2** — Intelligence: AI RCA suggestions, semantic search, heatmaps
- [ ] **Phase 3** — Insight: Coaching recommendations, badges, trend analytics
- [ ] **Phase 4** — Prediction: Release-risk prediction, quality forecast

---

## License

MIT