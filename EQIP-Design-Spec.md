# Engineering Quality Intelligence Platform (EQIP)

**Version:** 1.0
**Status:** Design + Requirements Specification

> Plain-language note: this document is written to be read by both engineers and non-engineers. Where a section could be confusing, there is a short "In plain words" line.

---

## 0. Key design decisions (read this first)

These are the core decisions this platform is built on. The most important one: quality is **not** scored by giving each story a fixed pool of points split between roles. A shared, fixed pool makes one person's gain another person's loss on the same story, which pushes people to fight over points instead of fixing quality — the same structure large companies (Microsoft, GE, Amazon) adopted and later dropped for hurting teamwork.

**Decisions:**

1. **No shared point pie.** Each role is scored on its **own absolute facts**. Two people on the same story can both score well.
2. **Ranking and badges** are built on those absolute facts, and every rank shows the facts behind it.
3. **AI suggests, humans decide.** AI proposes root cause / owner / severity. A human (the Engineering Manager) must sign off before it affects any rank or badge.
4. **Full-chain root cause.** The system traces a defect back through the chain (requirement → development → testing) and supports **shared / multi-cause** ownership, not a single villain.
5. **Diagnosis and coaching first.** The data's primary job is to show *where* quality breaks and to coach the right person. Feeding it to formal reviews is allowed but is a **separate, config-gated, low-weight input** — never the whole review, and always shown as raw facts, not just a number.

---

## 1. Vision

Traditional engineering metrics (velocity, story points, stories delivered) measure *activity*, not *quality*. EQIP measures quality: it captures every quality event across a story's life, traces defects to their true origin, and turns that into clear, factual feedback and dashboards that show where quality actually breaks down.

**The one question EQIP answers:** *Where does our engineering quality break, and what should we do about it?*

---

## 2. Guiding principles

1. Measure quality, not activity.
2. Reward prevention over correction.
3. Score each role on its **own** facts — never a shared, zero-sum pool.
4. Make every score **explainable**: show the facts behind it.
5. Use root-cause analysis to find the **true origin**, and support shared causes.
6. AI proposes; a human approves anything that affects a person's rank or badge.
7. Use the data to **diagnose and coach**, not to punish. Honest data depends on it being safe to tell the truth.
8. Keep a complete, immutable audit trail of every event.

---

## 3. Users and roles

| Role | Primary use |
|------|-------------|
| **Admin** | Create projects/sprints; import stories & bugs; manage users, teams, rules, weights; review disputes. |
| **Engineering Manager (EM)** | View team/sprint/release quality, trends, RCA reports, leaderboards; **sign off on AI root-cause/owner decisions**. |
| **Developer** | View own facts, story history, bug patterns, coaching recommendations, badges. |
| **Business Analyst (BA)** | View requirement-quality facts, clarification counts, missed-scenario traces, documentation quality. |
| **Tester** | View bugs found, edge cases, escaped defects, coverage contribution. |
| **Automation Engineer** | View coverage, execution success, stability, flaky tests. |

Access is role-based. A person sees their own facts in full; managers see aggregates and can drill into individuals for coaching.

---

## 4. Core scoring model (absolute, per-role)

**In plain words:** each role earns and loses points on its *own* record. Nobody is scored out of a shared pool, so helping a teammate never lowers your own score.

Each role has independent counters. A role's score is a transparent function of its own factual events. Weights are Admin-configurable.

### 4.1 Developer facts
- **Gains:** first-time-right code review, zero-defect story, reusable component created, performance/security improvement, early completion.
- **Loses:** validation bug, logic bug, high-severity defect, production defect, rework cycle, failed code review.

### 4.2 BA facts
- **Gains:** complete & clear acceptance criteria, well-documented story, edge cases covered up front, low clarification count.
- **Loses:** requirement gap traced to spec, wrong flow, missing acceptance criteria, late requirement changes.

### 4.3 Tester facts
- **Gains:** critical/edge/boundary/security/performance issues found *before release*, strong regression coverage.
- **Loses:** escaped production defect in their area, weak regression, confirmed false positive, incomplete/late testing.

### 4.4 Automation facts
- **Gains:** regression automated, stable scripts, high coverage, fast execution, CI integration.
- **Loses:** broken scripts, flaky tests, low coverage, maintenance backlog.

### 4.5 Score rules
- Scores are **additive and independent** per role. No fixed per-story total.
- Every gain/loss is stored as an immutable event with a reason and a link to the source (bug, review, RCA).
- **Earlier detection scores higher.** A bug caught in code review is worth more (positive to the finder) than the same class of bug caught in production.

---

## 5. Full-chain root cause and shared ownership

**In plain words:** when something breaks, trace it back through the whole chain to find where it *started* — and accept that often more than one role contributed.

### 5.1 The chain
```
Requirement (BA)  →  Development (Dev)  →  Code Review  →  Testing (Tester)  →  Automation  →  UAT  →  Release  →  Production
```

For each defect the system records: *what* went wrong (category), *where it was found* (discovery stage), and *why* (root cause), then maps the root cause to the chain stage that owns it.

### 5.2 Example (why the chain matters)
A production bug: "login accepts blank password."
- If the **requirement never stated** the validation rule → origin = BA/requirement.
- If the requirement stated it but the **code skipped** it → origin = Developer.
- If both had it but it **reached production untested** → origin = Testing.

Same symptom, three different origins, three different fixes. The chain finds the real one.

### 5.3 Shared ownership
Real defects often have several parents. The system supports **percentage ownership** across roles (e.g., BA 40% / Dev 40% / Tester 20%). The system does **not** force a single owner.

### 5.4 Root-cause categories
Requirement gap · Acceptance-criteria missing · Business logic · Validation · UI · API · Database · Security · Performance · Regression · Deployment · Environment · Automation gap · Testing gap · Customer change · Unknown.

### 5.5 Severity levels (each has a configurable weight)
Informational · Cosmetic · General · Medium · High · Critical · Production · Security · Performance · Data loss.

---

## 6. Ranking, badges, and recognition

**In plain words:** keep the fun and motivation. Rank on real facts, show the facts, and use it to celebrate — not to punish.

- **Leaderboards** (top developer / tester / BA / automation / team / module) — monthly, quarterly, yearly.
- **Monthly stars** and **badges**: Zero-Bug Champion, Edge-Case Hunter, Requirement Master, Automation Hero, Code Guardian, Quality Champion, Early Finisher, etc.
- **Rule:** a rank or badge **never** shows only a number. It always shows the facts behind it — e.g., "Rank #2 — 4 critical bugs caught pre-release, 0 escaped defects across 9 stories."
- Recognition (stars/badges) is for motivation. It is **decoupled** from compensation by default.

---

## 7. AI reasoning layer

**In plain words:** the AI reads the text and makes smart suggestions, but a human always has the final say on anything that affects a person.

### 7.1 What the AI does
Reads story documents, acceptance criteria, bug descriptions, and RCA comments, then **suggests**:
- Root cause + category
- Likely origin stage / owner (with shared-ownership split)
- Severity
- A **confidence score**
- Coaching recommendations (e.g., "Validation bugs up 42% this month in the Auth module — add a validation checklist to code review.")

### 7.2 Hard rule — human sign-off
Any AI suggestion that would affect a **rank, badge, or score** must be **reviewed and approved by the EM** before it counts. The AI is a suggestion engine, not a judge. Overrides are logged.

### 7.3 AI-powered semantic search
Natural-language search across all stories, bugs, and RCA notes — "show me all validation bugs in Auth in the last 3 sprints," "find defects similar to BUG-1245." Powered by vector embeddings in Postgres (see §9).

---

## 8. Data model (core entities)

### 8.1 Story
`story_id, title, epic, sprint, module, priority, complexity, story_points, acceptance_criteria, ba_id, developer_id, tester_id, automation_id, reviewer_id, status, estimated_date, completion_date, release, environment, attachments, documentation`

### 8.2 Bug
`bug_id, story_id, summary, description, severity, priority, environment, detected_by, detected_stage, assigned_to, root_cause, root_cause_category, origin_stage, ownership_split (JSON), bug_category, resolution, status, created_date, closed_date, ai_suggested (JSON), ai_confidence, human_approved_by, human_approved_at`

### 8.3 Quality event (immutable)
`event_id, story_id, role, actor_id, event_type, delta, reason, source_ref, ai_suggested, approved_by, created_at`

### 8.4 Role score (derived, never overwritten — recomputed from events)
`score_id, actor_id, role, period, module, computed_value, breakdown (JSON of contributing events)`

### 8.5 Embedding (for AI search)
`embedding_id, entity_type, entity_id, chunk_text, vector(1024), model_name, created_at`
(Dimension follows the embedding model — 1024 for BGE-M3. Store `model_name` so a re-embed is safe if you switch models.)

Excel/CSV/JSON/JIRA/Azure DevOps import must auto-populate Story and Bug fields.

---

## 9. Immutable audit trail

**In plain words:** nothing is ever secretly changed. Every score movement is a permanent, timestamped record you can replay.

- Every score change is an **append-only event**. Nothing is overwritten.
- A score is always **recomputable** by replaying its events, so any number can be explained end to end.

Example:
```
Story 1245 · Developer
  4.0  →  bug found        →  3.0
       →  root cause updated (shared, dev 40%) →  3.5
       →  bug closed       →  4.2
```

---

## 10. Interactive dashboards

**In plain words:** the data must let you *click into* the problem — from a module, to a bug type, to the exact stories and their root causes.

Design principle: **every number is a doorway.** Nothing is a dead-end figure; each card, bar, and cell drills down.

### 10.1 Executive / Quality dashboard
Cards: Quality Index, Sprint Quality, Release Quality, Production Defects, Escaped-Defect %, Early-Delivery %, Automation Coverage, Zero-Bug Stories.

### 10.2 Drill-down flow (the key feature you asked for)
```
Module heatmap (Auth is red)
   ↓ click
Bug-type breakdown for Auth: Validation 41% · UI 22% · Hygiene 18% · API 12% · Other 7%
   ↓ click "Validation"
Root-cause breakdown: Requirement gap 55% · Dev skipped 30% · Testing gap 15%
   ↓ click "Requirement gap"
List of the exact stories + RCA notes + who/what/when
```
This is the "data made meaningful" path: **count → category → root cause → specific stories.**

### 10.3 Views
- **Module heatmap** — colour by defect density / escaped defects.
- **Trend lines** — quality over time per module, per team, per bug category.
- **Chain view** — for any defect class, show where in the chain (BA/Dev/Test) it originates most.
- **Role dashboards** — each role sees its own facts, trends, and coaching tips.
- **Filters** everywhere: sprint, release, module, team, date range, severity, root cause.

### 10.4 Interactivity requirements
Real-time filtering (no page reload), cross-filtering (selecting a module filters all widgets), hover detail, click-through drill-down, exportable views.

---

## 11. Architecture

```
                React SPA (dashboards, drill-down, search UI)
                              │  HTTPS / JWT
                     ┌────────┴─────────┐
                     │   API Gateway    │
                     └────────┬─────────┘
        ┌───────────┬─────────┼──────────┬───────────────┐
        │           │         │          │               │
   Import Svc   Quality    Score      RCA / AI        Search Svc
   (Excel/JIRA/  Event    Engine     Reasoning       (semantic)
    ADO)         Engine   (per-role) (open models     │
                                      via router)
        └───────────┴─────────┼──────────┴───────────────┘
                              │
                   PostgreSQL + pgvector
              (system of record: events, bugs,
               stories, scores, embeddings)
                              │
                     Immutable audit log
```

- **Quality Event Engine:** the only writer of score events. Append-only.
- **Score Engine:** recomputes per-role scores by replaying events. Pure/deterministic.
- **RCA / AI Reasoning:** calls open-weight models (via a router / HF Inference) for suggestions; writes suggestions only, never final scores. Talks to the model through an OpenAI-compatible API so the model can be swapped by config.
- **Search Svc:** embeds text and runs vector similarity in pgvector.

---

## 12. Technology stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Frontend | **React** (TypeScript) | Dashboard, drill-down, search. |
| Charts | Recharts / Visx / ECharts | Cross-filtering + drill-down. |
| Graph views | Cytoscape.js | For chain / relationship views. |
| API | Node (NestJS) or Python (FastAPI) | Either fits; FastAPI pairs well with the AI layer. |
| Database | **PostgreSQL** | Single system of record. |
| Vector search | **pgvector** | Embeddings stored beside the data — no separate vector DB needed. |
| Embeddings | **BGE-M3** (open, ~1024-dim) | For semantic search / similar-bug lookup. Open license; you already validated this model. |
| Reasoning LLM | **Open-weight, permissive license only.** Default: **Qwen3** (Apache 2.0) for balanced RCA/classification; **DeepSeek V4** (MIT) when harder reasoning is needed; **GLM-5.2** (MIT) as an alternative. | RCA, owner suggestion, coaching text. Classification-grade work — a mid-size Qwen is enough; you do not need a frontier model. |
| LLM hosting | **Hugging Face Inference Endpoints** or a **router (e.g. OpenRouter / Together / Fireworks)** — OpenAI-compatible API | No OpenAI/GPT dependency. Router lets you send routine turns to a small/cheap model and hard RCA to a larger one. For strict data residency you can also self-host the same open weights on your Azure GPUs later. |
| Auth | Entra ID (SSO/MFA) | You already own it via M365. |
| Import | Excel / CSV / JSON / JIRA / Azure DevOps | API connectors are a later phase. |

> **Honesty note on model names + licensing:** Qwen3 (Apache 2.0), DeepSeek V4 (MIT), GLM-5.2 (MIT), and BGE-M3 are current, permissively-licensed open models as of **July 2026** (verified via Hugging Face model cards / open-LLM roundups). Two cautions: (1) open-model version names move even faster than closed ones — pin the exact model ID and **keep it in config**, never hard-coded; (2) **check the license before shipping** — "open" is not always commercial-safe. Avoid models with usage-cap or attribution clauses (e.g. Kimi's license adds an attribution requirement above certain thresholds) for a multi-tenant SaaS. Stick to Apache 2.0 / MIT. Final model choice should be made with your own small eval set (RCA-labelled bugs), not a public leaderboard.

---

## 13. Functional requirements

Each requirement has an acceptance criterion ("Done when…").

- **FR-1 Project & sprint setup.** Admin can create projects and sprints. *Done when* a project with sprints can be created and stories assigned.
- **FR-2 Story import.** Import stories from Excel/CSV/JSON/JIRA/ADO. *Done when* a file upload auto-populates all Story fields with a validation report for bad rows.
- **FR-3 Bug import.** Same sources for bugs. *Done when* bug rows map to the Bug model and link to their story.
- **FR-4 Per-role scoring.** Score each role on its own facts, no shared pool. *Done when* two roles on one story can both increase their score from the same story.
- **FR-5 Configurable weights.** Admin sets gain/loss/severity weights. *Done when* changing a weight re-derives scores from events without data loss.
- **FR-6 Full-chain RCA.** Record root cause and map to origin stage; support percentage ownership. *Done when* a single bug can be split across ≥2 roles and each role's score reflects its share.
- **FR-7 Earlier-detection bonus.** Earlier discovery scores higher. *Done when* the same bug class yields a higher finder score at code-review stage than at production.
- **FR-8 AI suggestion.** AI proposes root cause, owner, severity, confidence. *Done when* a bug shows AI suggestions with a confidence value.
- **FR-9 Mandatory human sign-off.** No AI suggestion affects a score/rank/badge until an EM approves. *Done when* an unapproved AI suggestion has zero effect on any score, and approval is logged.
- **FR-10 Semantic search.** Natural-language and similar-item search over stories/bugs/RCA. *Done when* a query returns ranked results by vector similarity plus keyword match.
- **FR-11 Immutable audit trail.** Every score change is append-only and replayable. *Done when* any current score can be reconstructed from its event history.
- **FR-12 Interactive dashboards.** Drill-down from module → bug type → root cause → stories, with cross-filtering. *Done when* clicking a module filters all widgets and the drill path reaches individual stories.
- **FR-13 Role dashboards.** Each role sees its own facts, trends, and coaching tips. *Done when* a developer sees only their facts plus recommendations.
- **FR-14 Ranking & badges.** Leaderboards and badges built on facts; every rank shows its evidence. *Done when* no rank/badge displays a bare number without its supporting facts.
- **FR-15 Coaching recommendations.** AI generates specific, area-based improvement tips. *Done when* a recommendation names a concrete area and action, not a rank.
- **FR-16 Dispute handling.** A person can dispute an AI-assigned root cause/owner; EM resolves. *Done when* a dispute is recorded, resolved, and the resolution is auditable.
- **FR-17 Review-input export (config-gated).** If enabled, export a person's **raw facts** (not a bare score) for review use, with an on-by-default warning. *Done when* the feature is off by default and, when on, exports facts + evidence rather than a single number.

---

## 14. Non-functional requirements

- **NFR-1 Security:** role-based access, project/tenant isolation, encryption at rest and in transit.
- **NFR-2 Auditability:** every score-affecting action is immutable and attributable.
- **NFR-3 Data residency:** LLM and data processing must respect geography (Azure Foundry region pinning). Relevant to LGPD / EU / India separation.
- **NFR-4 Explainability:** any score/rank must be traceable to its underlying events on demand.
- **NFR-5 Performance:** dashboard drill-down interactions respond in < 1s on typical data volumes.
- **NFR-6 Configurability:** rules, weights, and model names are config, not code.
- **NFR-7 Privacy of AI:** no person's data is used to train external models; use enterprise/no-retention API settings.

---

## 15. Guardrails (protect honest data)

**In plain words:** the whole system only works if people can tell the truth about causes without being punished. These rules protect that.

1. Root cause is used for **learning and coaching first**. Punishment breaks honesty.
2. **No shared, zero-sum scoring** — ever. Each role scores on its own facts.
3. **AI never has the final say** on anything affecting a person.
4. **Every rank/badge is explainable** — facts always shown.
5. **Review export is off by default**, low-weight, facts-not-numbers when on.
6. If a defect has several causes, record them as **shared** — do not force one owner.

---

## 16. Phased roadmap

**Phase 1 — Foundation**
Projects/sprints, story & bug import, per-role scoring, immutable event log, basic dashboards.

**Phase 2 — Intelligence**
AI root-cause/owner suggestions + human sign-off, semantic search (pgvector + embeddings), full-chain RCA, heatmaps & drill-down.

**Phase 3 — Insight**
Coaching recommendations, ranking/badges on facts, trend analytics, module risk view.

**Phase 4 — Prediction**
Release-risk prediction, quality forecast, org benchmarking, engineering-health index.

---

## 17. KPIs

Engineering Quality Index · Requirement Quality Index · Testing Quality Index · Automation Quality Index · Release Quality Index · Production Stability Index · Escaped-Defect Rate · Early-Delivery %.

---

## 18. Open decisions

1. **API framework** — NestJS (Node) vs FastAPI (Python). Recommendation: **FastAPI**, because the AI/RCA layer is Python-native and it keeps the reasoning code in one language.
2. **Review-input weight cap** — if review export (FR-17) is used, what maximum weight is allowed in a review? Recommend a hard, visible cap.
3. **Charting library** — ECharts vs Recharts vs Visx for the drill-down dashboards; pick one before Phase 1 UI work.

---

## 19. Success criteria

EQIP is successful when it can:
- Trace any defect to its true origin in the chain, with shared ownership where real.
- Produce fair, **explainable** per-role facts (no zero-sum fights).
- Drive coaching and process fixes that measurably reduce escaped defects.
- Surface quality bottlenecks by module/team/release via interactive drill-down.
- Motivate through fact-based recognition — without turning into a punishment engine.
