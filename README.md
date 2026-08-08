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
# 124 tests covering all 4 phases + sample stories/bugs
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
tests/test_core.py                  — Phase 1: Scoring engine, event recording, weight system
tests/test_phase2.py                — Phase 2: AI suggestions, semantic search, embeddings, chain RCA
tests/test_phase3.py                — Phase 3: Module risk, trend analytics, auto-badge evaluation
tests/test_phase4.py                — Phase 4: Forecast, health index, org benchmarking, trend prediction
tests/test_sample_stories_bugs.py   — Sample data: user stories, bugs, scoring, import, RCA keyword engine

Total: 124 tests — all passing ✅
```

---

## Sample User Stories

The project includes 10 realistic user stories modelling an e-commerce platform sprint. Full data lives in `backend/tests/sample_data.py`.

| ID | Title | Module | Points | Priority | Status |
|----|-------|--------|--------|----------|--------|
| US-101 | User Login with Email and Password | Auth | 5 | High | done |
| US-102 | Product Search with Filters | Search | 8 | High | done |
| US-103 | Add to Cart and Update Quantity | Cart | 5 | High | done |
| US-104 | Checkout with Stripe Payment | Checkout | 13 | Critical | in_progress |
| US-105 | Order History and Tracking | Orders | 5 | Medium | in_testing |
| US-106 | User Profile Management | Profile | 3 | Medium | done |
| US-107 | Admin Dashboard — Sales Analytics | Analytics | 8 | Low | backlog |
| US-108 | Push Notification Preferences | Notifications | 3 | Low | done |
| US-109 | Wishlist Functionality | Wishlist | 3 | Medium | done |
| US-110 | Password Reset via Email | Auth | 5 | High | done |

---

## Sample Bugs

12 sample bugs linked to the stories above, covering security, validation, performance, requirement gaps, and business logic issues.

| ID | Story | Summary | Severity | Root Cause | Origin | Status |
|----|-------|---------|----------|------------|--------|--------|
| BUG-201 | US-101 | Login allows SQL injection in email field | Critical | Security | Development | Fixed |
| BUG-202 | US-101 | Account lockout counter resets on page refresh | High | Validation | Development | Fixed |
| BUG-203 | US-102 | Price filter returns products outside selected range | Medium | Validation | Development | Open |
| BUG-204 | US-102 | Search returns 500 error for special characters | High | Validation | Development | Fixed |
| BUG-205 | US-103 | Cart allows adding more items than available stock | High | Validation | Requirement | Open |
| BUG-206 | US-103 | Cart total shows wrong amount with discount code | Critical | Business Logic | Requirement | Open |
| BUG-207 | US-104 | Double charge when user clicks Pay button twice | Critical | Validation | Development | Open |
| BUG-208 | US-104 | Order confirmation email not sent for guest checkout | Medium | Requirement Gap | Requirement | Open |
| BUG-209 | US-105 | Order history page crashes for users with 1000+ orders | High | Performance | Development | Open |
| BUG-210 | US-106 | Profile photo upload accepts files larger than 5 MB | Medium | Validation | Development | Fixed |
| BUG-211 | US-110 | Password reset link can be reused multiple times | High | Security | Development | Fixed |
| BUG-212 | US-109 | Wishlist does not enforce 50-item limit | Medium | AC Missing | Development | Open |

---

## Test Cases & Results

50 test cases validate the sample data and its integration with the EQIP scoring engine, import pipeline, and RCA keyword engine.

### Test Execution Results

```
$ cd backend && pytest tests/test_sample_stories_bugs.py -v

tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc001_all_stories_have_required_fields       PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc002_story_ids_are_unique                   PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc003_story_statuses_are_valid               PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc004_story_points_are_fibonacci             PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc005_acceptance_criteria_non_empty           PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc006_high_priority_stories_have_medium_or_higher_complexity PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc007_each_module_has_at_least_one_story      PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc008_done_stories_exist                      PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc009_story_id_format_correct                 PASSED
tests/test_sample_stories_bugs.py::TestUserStoryDataIntegrity::test_tc010_sample_stories_count                    PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc011_all_bugs_have_required_fields                 PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc012_bug_ids_are_unique                            PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc013_severities_map_to_enum                        PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc014_statuses_map_to_enum                          PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc015_root_cause_categories_valid                   PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc016_origin_stages_valid                           PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc017_critical_bugs_have_p0_priority                PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc018_every_bug_linked_to_story                     PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc019_bug_id_format_correct                         PASSED
tests/test_sample_stories_bugs.py::TestBugDataIntegrity::test_tc020_sample_bugs_count                             PASSED
tests/test_sample_stories_bugs.py::TestBugDistribution::test_tc021_multiple_severity_levels_covered               PASSED
tests/test_sample_stories_bugs.py::TestBugDistribution::test_tc022_multiple_root_cause_categories_covered         PASSED
tests/test_sample_stories_bugs.py::TestBugDistribution::test_tc023_bugs_detected_at_multiple_stages               PASSED
tests/test_sample_stories_bugs.py::TestBugDistribution::test_tc024_bugs_originate_from_multiple_stages            PASSED
tests/test_sample_stories_bugs.py::TestBugDistribution::test_tc025_at_least_one_security_bug                      PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc026_developer_gains_for_zero_defect_story    PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc027_developer_penalised_for_validation_bug   PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc028_tester_gains_for_critical_issue_found    PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc029_ba_penalised_for_requirement_gap         PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc030_tester_penalised_for_escaped_production_defect PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc031_ai_suggested_event_requires_approval     PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc032_independent_scoring_dev_and_tester_same_story PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc033_unapproved_ai_event_excluded_from_total  PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc034_security_improvement_positive_delta      PASSED
tests/test_sample_stories_bugs.py::TestScoringWithSampleData::test_tc035_automation_penalised_for_flaky_tests     PASSED
tests/test_sample_stories_bugs.py::TestImportPipeline::test_tc036_story_column_normalisation                      PASSED
tests/test_sample_stories_bugs.py::TestImportPipeline::test_tc037_bug_column_normalisation                        PASSED
tests/test_sample_stories_bugs.py::TestImportPipeline::test_tc038_story_data_can_build_dataframe                  PASSED
tests/test_sample_stories_bugs.py::TestImportPipeline::test_tc039_bug_data_can_build_dataframe                    PASSED
tests/test_sample_stories_bugs.py::TestImportPipeline::test_tc040_bug_severity_distribution                       PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc041_security_bugs_map_to_security_category   PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc042_production_detected_bugs_are_high_severity PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc043_stories_with_bugs_exist                  PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc044_stories_without_bugs_exist               PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc045_requirement_origin_bugs_trace_to_ba      PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc046_development_origin_bugs_trace_to_developer PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc047_open_vs_fixed_bug_ratio                  PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc048_keyword_rule_engine_detects_validation   PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc049_keyword_rule_engine_detects_security     PASSED
tests/test_sample_stories_bugs.py::TestCrossCuttingScenarios::test_tc050_keyword_rule_engine_detects_performance  PASSED

50 passed ✅
```

### Test Case Summary

| # | Test ID | Area | Description | Result |
|---|---------|------|-------------|--------|
| 1 | TC-001 | Story Data | All stories have required fields | ✅ Pass |
| 2 | TC-002 | Story Data | Story IDs are unique | ✅ Pass |
| 3 | TC-003 | Story Data | Statuses map to valid enum | ✅ Pass |
| 4 | TC-004 | Story Data | Story points follow Fibonacci | ✅ Pass |
| 5 | TC-005 | Story Data | Acceptance criteria non-empty | ✅ Pass |
| 6 | TC-006 | Story Data | High-priority stories have ≥ Medium complexity | ✅ Pass |
| 7 | TC-007 | Story Data | Multiple modules covered (≥5) | ✅ Pass |
| 8 | TC-008 | Story Data | Done stories exist for scoring | ✅ Pass |
| 9 | TC-009 | Story Data | Story ID format `US-NNN` | ✅ Pass |
| 10 | TC-010 | Story Data | ≥10 sample stories | ✅ Pass |
| 11 | TC-011 | Bug Data | All bugs have required fields | ✅ Pass |
| 12 | TC-012 | Bug Data | Bug IDs are unique | ✅ Pass |
| 13 | TC-013 | Bug Data | Severities map to enum | ✅ Pass |
| 14 | TC-014 | Bug Data | Statuses map to enum | ✅ Pass |
| 15 | TC-015 | Bug Data | Root cause categories valid | ✅ Pass |
| 16 | TC-016 | Bug Data | Origin stages valid | ✅ Pass |
| 17 | TC-017 | Bug Data | Critical bugs have P0 priority | ✅ Pass |
| 18 | TC-018 | Bug Data | Every bug linked to a story | ✅ Pass |
| 19 | TC-019 | Bug Data | Bug ID format `BUG-NNN` | ✅ Pass |
| 20 | TC-020 | Bug Data | ≥10 sample bugs | ✅ Pass |
| 21 | TC-021 | Distribution | ≥3 severity levels covered | ✅ Pass |
| 22 | TC-022 | Distribution | ≥4 root cause categories | ✅ Pass |
| 23 | TC-023 | Distribution | ≥3 detected stages | ✅ Pass |
| 24 | TC-024 | Distribution | ≥2 origin stages | ✅ Pass |
| 25 | TC-025 | Distribution | ≥1 security bug | ✅ Pass |
| 26 | TC-026 | Scoring | Developer gains for zero-defect story | ✅ Pass |
| 27 | TC-027 | Scoring | Developer penalised for validation bug | ✅ Pass |
| 28 | TC-028 | Scoring | Tester gains for critical issue found | ✅ Pass |
| 29 | TC-029 | Scoring | BA penalised for requirement gap | ✅ Pass |
| 30 | TC-030 | Scoring | Tester penalised for escaped defect | ✅ Pass |
| 31 | TC-031 | Scoring | AI-suggested event requires approval | ✅ Pass |
| 32 | TC-032 | Scoring | Independent scoring — no zero-sum | ✅ Pass |
| 33 | TC-033 | Scoring | Unapproved AI events excluded | ✅ Pass |
| 34 | TC-034 | Scoring | Security improvement positive delta | ✅ Pass |
| 35 | TC-035 | Scoring | Automation penalised for flaky tests | ✅ Pass |
| 36 | TC-036 | Import | Story column normalisation | ✅ Pass |
| 37 | TC-037 | Import | Bug column normalisation | ✅ Pass |
| 38 | TC-038 | Import | Stories load into DataFrame | ✅ Pass |
| 39 | TC-039 | Import | Bugs load into DataFrame | ✅ Pass |
| 40 | TC-040 | Import | Bug severity distribution | ✅ Pass |
| 41 | TC-041 | Cross-cutting | Security bugs are critical/high | ✅ Pass |
| 42 | TC-042 | Cross-cutting | Production bugs are high severity | ✅ Pass |
| 43 | TC-043 | Cross-cutting | Stories with bugs exist | ✅ Pass |
| 44 | TC-044 | Cross-cutting | Stories without bugs exist | ✅ Pass |
| 45 | TC-045 | Cross-cutting | Requirement-origin bugs trace to BA | ✅ Pass |
| 46 | TC-046 | Cross-cutting | Development-origin bugs trace to Dev | ✅ Pass |
| 47 | TC-047 | Cross-cutting | Open and fixed bugs both present | ✅ Pass |
| 48 | TC-048 | RCA Engine | Keyword engine detects validation | ✅ Pass |
| 49 | TC-049 | RCA Engine | Keyword engine detects security | ✅ Pass |
| 50 | TC-050 | RCA Engine | Keyword engine detects performance | ✅ Pass |

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