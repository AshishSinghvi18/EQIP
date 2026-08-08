# Engineering Quality Intelligence Platform (EQIP)

**Version:** 1.1
**Status:** Design + Requirements Specification
**Changed in this version:** Added a per-participant 10-point story score (every role gets its own 10 on each story — no shared pool), High/Medium/Low story classification, story onboarding data requirements, and an extended AI bug-reasoning layer (silly miss / critical miss / info-not-in-story / missing unit test / wrong test cases). See the changelog in §0.1.

> **Plain-language note:** this document is written to be read by both engineers and non-engineers. Where a section could be confusing, there is a short *"In plain words"* line.

---

## 0. Key design decisions (read this first)

These are the core decisions this platform is built on. The most important one: **quality is not scored by giving each story a fixed pool of points split between people.** A shared, fixed pool makes one person's gain another person's loss on the same story, which pushes people to fight over points instead of fixing quality — the same structure large companies (Microsoft, GE, Amazon) adopted and later dropped for hurting teamwork.

Decisions:

1. **No shared point pie between people.** Each *role* is scored on its own absolute facts. Two people on the same story can both score well.
2. **Each participant gets their own 10 points on every story.** *(New in v1.1.)* The 10 points are **not** a shared pool split between people. Every participating role (BA, Developer, Tester, Automation) starts each story at **10.0** and loses points **only for their own attributed faults**. Two people on the same story can both keep a perfect 10. The story's overall High/Medium/Low class is decided separately, by escalations and serious bugs (§4.7). See §4.6.
3. **Ranking and badges** are built on those absolute facts, and every rank shows the facts behind it.
4. **AI suggests, humans decide.** AI proposes root cause / owner / severity / bug-reasoning class. A human (the Engineering Manager) must sign off before it affects any story class, rank, or badge.
5. **Full-chain root cause.** The system traces a defect back through the chain (requirement → development → testing) and supports shared / multi-cause ownership, not a single villain.
6. **Diagnosis and coaching first.** The data's primary job is to show where quality breaks and to coach the right person. Feeding it to formal reviews is allowed but is a separate, config-gated, low-weight input — never the whole review, and always shown as raw facts, not just a number.

### 0.1 Changelog (v1.0 → v1.1)

| Area | Change |
|------|--------|
| §4.6 Per-role story score | **New.** Each participating role gets its own 10-point score on every story; no shared pool. |
| §4.7 Story classification | **New.** High / Medium / Low rules (escalations + serious-bug driven). |
| §4.8 Onboarding data gate | **New.** A story is only scored once it has description, bug list, dev unit tests, and BA/tester test cases. |
| §7.4 Bug-reasoning classes | **New.** silly miss · critical miss · info-not-in-story · missing unit test · test cases wrongly generated. |
| §8.1 / §8.2 / §8.6 Data model | **Updated + new** fields; per-role-story score + story-class entities. |
| §10.5 Story-quality dashboard | **New.** Total onboarded, class breakdown, "where we fall" bug-reasoning view. |
| §16 Roadmap | **Updated.** Added built-in sprint planning as a future phase (removes separate onboarding). |

> **Design decision (confirmed):** The "10 points per story" is **assigned to every participant individually** — each role starts at 10 on each story and is deducted only for its own faults. There is **no shared pool** and no zero-sum split between people, consistent with the founding rule above.

---

## 1. Vision

Traditional engineering metrics (velocity, story points, stories delivered) measure activity, not quality. EQIP measures **quality**: it captures every quality event across a story's life, traces defects to their true origin, and turns that into clear, factual feedback and dashboards that show where quality actually breaks down.

**The one question EQIP answers:** *Where does our engineering quality break, and what should we do about it?*

---

## 2. Guiding principles

- Measure quality, not activity.
- Reward prevention over correction.
- Score each **role** on its own facts — never a shared, zero-sum pool between people.
- Give each participant their **own 0–10 score on every story** (no shared pool), and rank the **story itself** High/Medium/Low by escalations and serious bugs.
- Make every score explainable: show the facts behind it.
- Use root-cause analysis to find the true origin, and support shared causes.
- AI proposes; a human approves anything that affects a person's rank/badge or a story's class.
- Use the data to diagnose and coach, not to punish. Honest data depends on it being safe to tell the truth.
- Keep a complete, immutable audit trail of every event.

---

## 3. Users and roles

| Role | Primary use |
|------|-------------|
| **Admin** | Create projects/sprints; import/onboard stories & bugs; manage users, teams, rules, weights, thresholds; review disputes. |
| **Engineering Manager (EM)** | View team/sprint/release quality, trends, RCA reports, leaderboards, **story classifications**; sign off on AI root-cause/owner/reasoning decisions. |
| **Developer** | View own facts, story history, bug patterns, coaching recommendations, badges. |
| **Business Analyst (BA)** | View requirement-quality facts, clarification counts, missed-scenario traces, documentation quality. |
| **Tester** | View bugs found, edge cases, escaped defects, coverage contribution. |
| **Automation Engineer** | View coverage, execution success, stability, flaky tests. |

Access is role-based. A person sees their own facts in full; managers see aggregates and can drill into individuals for coaching.

---

## 4. Core scoring model

### 4.1–4.5 Per-role absolute scoring (unchanged from v1.0)

> **In plain words:** each role earns and loses points on its own record. Nobody is scored out of a shared pool, so helping a teammate never lowers your own score.

- **Developer facts** — Gains: first-time-right review, zero-defect story, reusable component, perf/security improvement, early completion. Loses: validation bug, logic bug, high-severity defect, production defect, rework cycle, failed review.
- **BA facts** — Gains: complete/clear acceptance criteria, well-documented story, edge cases up front, low clarification count. Loses: requirement gap traced to spec, wrong flow, missing acceptance criteria, late requirement changes.
- **Tester facts** — Gains: critical/edge/boundary/security/perf issues found before release, strong regression. Loses: escaped production defect in their area, weak regression, confirmed false positive, incomplete/late testing.
- **Automation facts** — Gains: regression automated, stable scripts, high coverage, fast execution, CI integration. Loses: broken scripts, flaky tests, low coverage, maintenance backlog.
- **Score rules** — additive, independent per role; no fixed per-story total between people; every gain/loss is an immutable event with a reason and source link; **earlier detection scores higher** (a bug caught in review beats the same bug caught in production).

### 4.6 Per-role story score — *New in v1.1*

> **In plain words:** on every story, each person gets their own 10 points. You only lose your own points for your own mistakes. My 10 and your 10 are separate — me losing a point never gives you one, and never takes one from you.

**Rules:**

- On each **onboarded** story, **every participating role** (BA, Developer, Tester, Automation) starts with **10.0 points** — their own, independent score for that story.
- A confirmed defect or escalation is **attributed** (via the reasoning class §7.4 and root-cause chain §5) to the role(s) responsible. The deduction applies **only to that role's 10** on that story.
- If a defect has **shared ownership** (e.g., BA 40% / Dev 40% / Tester 20%), the deduction is split by those percentages across the responsible roles only. Roles not at fault are untouched.
- A role's story score floors at **0.0** (never negative).
- All per-role story scores are **derived and recomputed by replaying events** — never overwritten (consistent with §9).
- A role's per-story deductions also flow into that role's cumulative §4.1–4.4 scorecard. Nothing here is zero-sum: one role's deduction never changes another role's score.

**Why this is not a shared pool:** the story does not have one 10 split between people. Each person carries their own 10 on the story. On a clean story, everyone keeps 10. On a flawed story, only the responsible role(s) lose points, in proportion to their share of the cause.

**Illustrative per-role deduction table (Admin-configurable — proposed defaults, not fixed):**

| Reasoning class (§7.4) | Role that loses points | Suggested deduction (from that role's 10) |
|------------------------|------------------------|-------------------------------------------|
| Silly miss | Developer | −0.5 to −1.0 |
| Critical miss | Developer / design | −2.0 to −4.0 |
| Information not available in story | BA | −1.5 to −3.0 |
| Missing unit testing | Developer | −1.0 to −2.0 |
| Test cases wrongly generated | Tester / BA | −1.0 to −2.0 |
| Escalation (any) | Traced per case to the responsible role(s) | −2.0 additional |

> **Inference flag:** the numbers above are my proposed starting weights, not from the original spec. Tune them against a labelled sample before trusting the distribution.

**Story Quality Rollup (display only):** for sorting the "total onboarded" list and colouring heatmaps, the system shows a per-story rollup = the **average of participating roles' story scores**. This is a summary for display and sorting only — it does **not** create any coupling between people (averaging independent scores is not zero-sum). Fault always lives on the individual role scores.

### 4.7 Story classification: High / Medium / Low — *New in v1.1*

> **In plain words:** High = clean story (no escalations, no serious bugs). Medium = only minor bugs. Low = something serious or escalated happened.

The **story's** class is decided by the hard gates you specified (escalations + serious bugs), with the rollup (§4.6) as a tiebreak. Thresholds are Admin-configurable; proposed defaults:

| Class | Rule (all conditions must hold) |
|-------|---------------------------------|
| **High** | 0 escalations **AND** 0 serious bugs *(Critical / Production / Security / Data-loss severity)* **AND** rollup ≥ 8.0 |
| **Medium** | 0 escalations **AND** 0 serious bugs **AND** 5.0 ≤ rollup < 8.0 (non-serious bugs allowed) |
| **Low** | Any escalation **OR** any serious bug **OR** rollup < 5.0 |

**Complexity normalisation (optional, config-gated):** a high-complexity story (high `story_points`) may be graded on a slightly more forgiving curve, so a hard story with a couple of minor bugs is not unfairly marked Low. Off by default; when on, the adjustment is shown on the story's facts, never hidden.

### 4.8 Onboarding data gate — *New in v1.1*

> **In plain words:** we don't score a story until we actually have the data to score it fairly.

A story is **eligible for quality scoring** only when it has all four data points:

1. **Story description** — with content, screenshots, and attachments.
2. **Bug list** — every bug raised against the story, with descriptions (an explicit "zero bugs" is a valid, recorded state).
3. **Developer unit test cases** — list or reference.
4. **BA / Tester test cases** — list or reference.

A story missing any of these is flagged **`Insufficient data`** (not scored, not classified) and appears on a "needs data" queue rather than being silently graded on partial information.

---

## 5. Full-chain root cause and shared ownership

> **In plain words:** when something breaks, trace it back through the whole chain to find where it started — and accept that often more than one role contributed.

**5.1 The chain:** Requirement (BA) → Development (Dev) → Code Review → Testing (Tester) → Automation → UAT → Release → Production.

**5.2 Example:** production bug "login accepts blank password." If the requirement never stated the rule → origin = BA. If it was stated but code skipped it → origin = Developer. If both had it but it shipped untested → origin = Testing. Same symptom, three origins, three fixes.

**5.3 Shared ownership:** the system supports percentage ownership across roles (e.g., BA 40% / Dev 40% / Tester 20%). It does not force a single owner. Per-role story deductions (§4.6) are split by the same percentages — only across the responsible roles.

**5.4 Root-cause categories:** Requirement gap · Acceptance-criteria missing · Business logic · Validation · UI · API · Database · Security · Performance · Regression · Deployment · Environment · Automation gap · Testing gap · Customer change · Unknown.

**5.5 Severity levels (each configurable weight):** Informational · Cosmetic · General · Medium · High · Critical · Production · Security · Performance · Data loss.
*Serious severities* (used by the High/Medium/Low gate in §4.7): **Critical, Production, Security, Data loss.**

---

## 6. Ranking, badges, and recognition

> **In plain words:** keep the fun and motivation. Rank on real facts, show the facts, use it to celebrate — not to punish.

- Leaderboards (top developer / tester / BA / automation / team / module) — monthly, quarterly, yearly.
- Monthly stars and badges: Zero-Bug Champion, Edge-Case Hunter, Requirement Master, Automation Hero, Code Guardian, Quality Champion, Early Finisher, etc.
- **Rule:** a rank or badge never shows only a number. It always shows the facts behind it — e.g., *"Rank #2 — 4 critical bugs caught pre-release, 0 escaped defects across 9 stories."*
- Recognition is for motivation and is decoupled from compensation by default.

---

## 7. AI reasoning layer

> **In plain words:** the AI reads the text and makes smart suggestions, but a human always has the final say on anything that affects a person or a story's grade.

**7.1 What the AI does** — reads story documents, acceptance criteria, bug descriptions and RCA comments, then suggests: root cause + category; likely origin stage / owner (with shared split); severity; **bug-reasoning class (§7.4)**; a confidence score; and coaching recommendations.

**7.2 Hard rule — human sign-off** — any AI suggestion that would affect a rank, badge, score, **or story class** must be reviewed and approved by the EM before it counts. The AI is a suggestion engine, not a judge. Overrides are logged.

**7.3 AI-powered semantic search** — natural-language search across all stories, bugs and RCA notes (e.g., *"show me all validation bugs in Auth in the last 3 sprints"*). Powered by vector embeddings in Postgres (see §12).

### 7.4 Bug-reasoning classes — *New in v1.1*

> **In plain words:** for each bug, the AI proposes *why* it happened, in words the whole team understands. This is the "where do we fall?" signal, and it decides whose 10 loses points.

For every bug, the AI proposes one primary reasoning class (and may flag a secondary):

| Class | Meaning | Role that loses points | Coaching direction |
|-------|---------|------------------------|--------------------|
| **Silly miss** | An easily avoidable oversight — typo, obvious validation, careless slip. | Developer | Checklists, self-review discipline. |
| **Critical miss** | A serious defect in core logic, security, or data handling. | Developer / design | Design review, threat/edge modelling. |
| **Information not available in story** | The story didn't contain what was needed to build it right. | BA | Acceptance-criteria and edge-case completeness. |
| **Missing unit testing** | The developer shipped without unit coverage for this path. | Developer | Definition-of-done gating on unit tests. |
| **Test cases wrongly generated** | The BA/tester test cases were wrong, or missed the scenario. | Tester / BA | Test-design review, scenario coverage. |

Each class maps to (a) a **deduction on the responsible role's 10 for that story** (§4.6) and (b) the same attribution feeding that role's cumulative scorecard (§4.1–4.4). Both require EM sign-off (§7.2) before counting.

---

## 8. Data model (core entities)

### 8.1 Story *(updated in v1.1)*
`story_id, title, epic, sprint, module, priority, complexity, story_points, acceptance_criteria, ba_id, developer_id, tester_id, automation_id, reviewer_id, status, estimated_date, completion_date, release, environment,`
`description, attachments, screenshots, documentation,`
`unit_test_cases (JSON/list — from developers),`
`ba_test_cases (JSON/list — from BA/testers),`
`escalations (JSON/list),`
`onboarding_complete (bool), completeness_gaps (list),`
`story_rollup (derived, display-only), quality_class (derived: High/Medium/Low)`

### 8.2 Bug *(updated in v1.1)*
`bug_id, story_id, summary, description, severity, priority, environment, detected_by, detected_stage, assigned_to, root_cause, root_cause_category, origin_stage, ownership_split (JSON), bug_category, resolution, status, created_date, closed_date,`
`reasoning_class (silly_miss | critical_miss | info_not_in_story | missing_unit_test | wrong_test_cases),`
`ai_suggested (JSON), ai_confidence, human_approved_by, human_approved_at`

### 8.3 Quality event (immutable)
`event_id, story_id, role, actor_id, event_type, delta, reason, source_ref, ai_suggested, approved_by, created_at`

### 8.4 Role score (cumulative, derived, recomputed from events)
`score_id, actor_id, role, period, module, computed_value, breakdown (JSON)`

### 8.5 Embedding (for AI search)
`embedding_id, entity_type, entity_id, chunk_text, vector(1024), model_name, created_at`
*(Dimension follows the embedding model — 1024 for BGE-M3. Store `model_name` so a re-embed is safe if you switch models.)*

### 8.6 Per-role story score (derived, recomputed — *New in v1.1*)
`rss_id, story_id, role, actor_id, score (0–10), breakdown (JSON of that role's deductions on this story), computed_at`
*(One row per participating role per story. Never overwritten. Replayable from events. This is the "everyone gets their own 10" record.)*

### 8.6b Story class (derived, recomputed — *New in v1.1*)
`sc_id, story_id, quality_class, rollup (avg of role scores, display-only), serious_bug_count, escalation_count, computed_at`

> Excel / CSV / JSON / JIRA / Azure DevOps import must auto-populate Story and Bug fields, including the new onboarding data points where the source has them.

---

## 9. Immutable audit trail

> **In plain words:** nothing is ever secretly changed. Every score movement — each person's per-story 10, their cumulative score, and the story class — is a permanent, timestamped record you can replay.

- Every score change is an append-only event. Nothing is overwritten.
- Any score is recomputable by replaying its events, so any number can be explained end to end.

```
Story 1245 — per-role story scores (each independent, no shared pool)

  BA      10.0 → info not in story (BA, −1.5)      → 8.5
  Dev     10.0 → silly miss (Dev, −0.5)            → 9.5
                → missing unit test (Dev, −1.0)    → 8.5
  Tester  10.0 → (no faults)                       → 10.0

  Story class: an escalation was raised → LOW
  (Dev losing points never changed the Tester's 10.)
```

---

## 10. Interactive dashboards

> **In plain words:** the data must let you click into the problem — from a module, to a bug type, to the exact stories and their root causes.

**Design principle:** *every number is a doorway.* Nothing is a dead-end figure; each card, bar and cell drills down.

**10.1 Executive / Quality dashboard** — Cards: Quality Index, Sprint Quality, Release Quality, Production Defects, Escaped-Defect %, Early-Delivery %, Automation Coverage, Zero-Bug Stories.

**10.2 Drill-down flow:** Module heatmap → bug-type breakdown → root-cause breakdown → exact stories + RCA notes. (count → category → root cause → specific stories.)

**10.3 Views** — module heatmap, trend lines, chain view, role dashboards; filters everywhere (sprint, release, module, team, date range, severity, root cause).

**10.4 Interactivity** — real-time filtering, cross-filtering, hover detail, click-through drill-down, exportable views.

### 10.5 Story-quality dashboard — *New in v1.1*

- **Total stories onboarded** — count card (with an "insufficient data" sub-count from §4.8).
- **Quality-class breakdown** — High / Medium / Low, as a stacked bar or donut; click a class to list its stories.
- **"Where we fall" — bug-reasoning breakdown** — the five §7.4 classes across all bugs (e.g., *Silly miss 34% · Missing unit testing 22% · Info not in story 20% · Wrong test cases 14% · Critical miss 10%*). This is the primary "where do we need to improve" view.
- **Per-role contribution on a story** — open any story to see each participant's 10 and what they lost, side by side.
- **Escalation view** — stories with escalations, drill to the traced origin.
- **Class trend** — High/Medium/Low mix per sprint, to see whether quality is improving.
- **Drill path:** class → reasoning breakdown → the exact stories, bugs, per-role scores and RCA notes behind it.

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
   Import/       Quality    Score      RCA / AI        Search Svc
   Onboard Svc   Event     Engine     Reasoning       (semantic)
   (Excel/JIRA/  Engine    (per-role  (open models
    ADO + native)          + per-role via router)
                           per-story
                           + story class)
        └───────────┴─────────┼──────────┴───────────────┘
                              │
                   PostgreSQL + pgvector
              (system of record: events, bugs, stories,
               role scores, per-role story scores,
               story class, embeddings)
                              │
                     Immutable audit log
```

- **Quality Event Engine** — the only writer of score events. Append-only.
- **Score Engine** — recomputes cumulative per-role scores, **per-role per-story scores**, and story class by replaying events. Pure/deterministic.
- **RCA / AI Reasoning** — calls open-weight models for suggestions (root cause, owner, severity, reasoning class); writes suggestions only, never final scores. OpenAI-compatible API so the model can be swapped by config.
- **Search Svc** — embeds text and runs vector similarity in pgvector.

---

## 12. Technology stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Frontend | React (TypeScript) | Dashboard, drill-down, search. |
| Charts | Recharts / Visx / ECharts | Cross-filtering + drill-down. |
| Graph views | Cytoscape.js | Chain / relationship views. |
| API | FastAPI (Python) *(recommended)* or NestJS (Node) | FastAPI keeps the AI layer in one language. |
| Database | PostgreSQL | Single system of record. |
| Vector search | pgvector | Embeddings beside the data — no separate vector DB. |
| Embeddings | BGE-M3 (open, ~1024-dim) | Semantic search / similar-bug lookup. Permissive license. |
| Reasoning LLM | Open-weight, permissive only. Default Qwen3 (Apache 2.0); DeepSeek V4 (MIT) for harder reasoning; GLM-5.2 (MIT) alternative. | RCA, owner + reasoning-class suggestion, coaching text. Classification-grade — a mid-size model is enough. |
| LLM hosting | HF Inference Endpoints or a router (OpenRouter / Together / Fireworks), OpenAI-compatible | No OpenAI/GPT dependency. Self-host on Azure GPUs later for strict residency. |
| Auth | Entra ID (SSO/MFA) | Already owned via M365. |
| Import / Onboard | Excel / CSV / JSON / JIRA / Azure DevOps, plus native creation | API connectors are a later phase. |

> **Licensing caution (unchanged from v1.0):** open-model version names move fast — pin the exact model ID in config, never hard-code. Check the license before shipping ("open" ≠ commercial-safe); avoid usage-cap / attribution clauses for a multi-tenant SaaS. Stick to Apache 2.0 / MIT. Final choice via your own labelled eval set, not a public leaderboard.

---

## 13. Functional requirements

*(FR-1 to FR-17 from v1.0 retained. New/updated requirements below.)*

- **FR-1** Project & sprint setup. *Done when a project with sprints can be created and stories assigned.*
- **FR-2** Story import/onboarding. *Done when a file upload auto-populates Story fields with a validation report for bad rows.*
- **FR-3** Bug import. *Done when bug rows map to the Bug model and link to their story.*
- **FR-4** Per-role scoring (no shared pool). *Done when two roles on one story can both increase their score from the same story.*
- **FR-5** Configurable weights. *Done when changing a weight re-derives scores from events without data loss.*
- **FR-6** Full-chain RCA with % ownership. *Done when a bug can be split across ≥2 roles and each score reflects its share.*
- **FR-7** Earlier-detection bonus. *Done when the same bug class scores higher at review than at production.*
- **FR-8** AI suggestion (root cause, owner, severity, confidence). *Done when a bug shows AI suggestions with a confidence value.*
- **FR-9** Mandatory human sign-off. *Done when an unapproved AI suggestion has zero effect and approval is logged.*
- **FR-10** Semantic search. *Done when a query returns ranked vector + keyword results.*
- **FR-11** Immutable audit trail. *Done when any current score can be reconstructed from its event history.*
- **FR-12** Interactive dashboards with drill-down + cross-filtering. *Done when clicking a module filters all widgets down to individual stories.*
- **FR-13** Role dashboards. *Done when a developer sees only their facts plus recommendations.*
- **FR-14** Ranking & badges on facts. *Done when no rank/badge shows a bare number without supporting facts.*
- **FR-15** Coaching recommendations. *Done when a recommendation names a concrete area and action.*
- **FR-16** Dispute handling. *Done when a dispute is recorded, resolved, and auditable.*
- **FR-17** Review-input export (config-gated, off by default). *Done when it exports facts + evidence, never a bare number.*

**New in v1.1:**

- **FR-18** Story onboarding data gate. Capture description + screenshots, bug list, dev unit tests, and BA/tester test cases. *Done when a story missing any of the four is flagged `Insufficient data` and excluded from scoring until complete.*
- **FR-19** Per-role story score (everyone gets their own 10). Each participating role starts at 10 on each story and loses points only for its own attributed faults. *Done when a defect attributed to one role reduces only that role's story score and never changes another role's score on the same story.*
- **FR-20** Story classification. Derive High / Medium / Low from escalation + serious-bug gates (rollup as tiebreak). *Done when any story with an escalation or a serious bug is never classified High.*
- **FR-21** Bug-reasoning classification. AI proposes one of the five §7.4 classes per bug; EM signs off. *Done when each approved bug carries a reasoning class that deducts from the responsible role's story-10 and cumulative score.*
- **FR-22** "Total onboarded" + "where we fall" dashboard. *Done when the dashboard shows total onboarded stories, the High/Medium/Low mix, and the five-class bug-reasoning breakdown, each drillable to the underlying stories and per-role scores.*

---

## 14. Non-functional requirements

- **NFR-1 Security** — role-based access, tenant isolation, encryption at rest and in transit.
- **NFR-2 Auditability** — every score-affecting action is immutable and attributable.
- **NFR-3 Data residency** — LLM and data processing respect geography (Azure region pinning; LGPD / EU / India separation).
- **NFR-4 Explainability** — any score/rank/**story class** traceable to its underlying events on demand.
- **NFR-5 Performance** — dashboard drill-down responds in < 1s on typical volumes.
- **NFR-6 Configurability** — rules, weights, **classification thresholds**, and model names are config, not code.
- **NFR-7 Privacy of AI** — no person's data trains external models; enterprise/no-retention API settings.

---

## 15. Guardrails (protect honest data)

> **In plain words:** the whole system only works if people can tell the truth about causes without being punished.

- Root cause is used for learning and coaching first. Punishment breaks honesty.
- **No shared, zero-sum scoring between people — ever.** Each participant has their own 10 on a story; one person's deduction never moves another person's score.
- AI never has the final say on anything affecting a person or a story class.
- Every rank/badge/**story class** is explainable — facts always shown.
- Review export is off by default, low-weight, facts-not-numbers when on.
- Multi-cause defects are recorded as shared — no forced single owner.

---

## 16. Phased roadmap

- **Phase 1 — Foundation:** projects/sprints, story & bug onboarding **with the four data points (§4.8)**, per-role scoring, **per-role story 10s + High/Medium/Low classification**, immutable event log, basic dashboards + **total-onboarded and class views**.
- **Phase 2 — Intelligence:** AI root-cause/owner/**reasoning-class** suggestions + human sign-off, semantic search (pgvector), full-chain RCA, heatmaps & drill-down, **"where we fall" bug-reasoning view**.
- **Phase 3 — Insight:** coaching recommendations, ranking/badges on facts, trend analytics, module risk view.
- **Phase 4 — Prediction:** release-risk prediction, quality forecast, org benchmarking, engineering-health index.
- **Phase 5 — Built-in sprint planning *(New in v1.1):*** create and plan stories natively inside EQIP so they no longer need to be onboarded/imported separately. This turns onboarding from an import step into native story creation, and lets quality scoring run from the moment a story is planned.

---

## 17. KPIs

Engineering Quality Index · Requirement Quality Index · Testing Quality Index · Automation Quality Index · Release Quality Index · Production Stability Index · Escaped-Defect Rate · Early-Delivery % · **High/Medium/Low story mix (new)** · **Bug-reasoning distribution (new)**.

---

## 18. Open decisions

1. **The "10 points" model** — **resolved:** each participant gets their own 10 per story, no shared pool (§4.6).
2. **Classification thresholds** — confirm or tune the High/Medium/Low cut-offs (§4.7); they are proposed defaults, not validated numbers.
3. **Rollup for sorting** — confirm "average of role scores" is the right display rollup, or prefer "lowest role score" (weakest-link) for the story sort.
4. **Complexity normalisation** — decide whether to enable the config-gated forgiving curve for high-complexity stories (§4.7).
5. **Deduction weights** — set real values for §4.6 against a labelled sample of bugs.
6. **API framework** — FastAPI (recommended) vs NestJS.
7. **Charting library** — ECharts vs Recharts vs Visx.
8. **Review-input weight cap** — hard, visible cap if FR-17 is used.

---

## 19. Success criteria

EQIP is successful when it can:

- Onboard a story with its full data set and refuse to score it when data is missing.
- Give every participant their own fair, explainable 10 on each story, with no shared pool and no zero-sum fights.
- Give every story a fair, explainable **High/Medium/Low** grade driven by escalations and serious bugs.
- Trace any defect to its true origin in the chain, with shared ownership where real.
- Tell the team, in plain words, **where they fall** (the five bug-reasoning classes) and what to improve.
- Drive coaching and process fixes that measurably reduce escaped defects and shift the High/Medium/Low mix upward over time.
- Motivate through fact-based recognition — without turning into a punishment engine.
