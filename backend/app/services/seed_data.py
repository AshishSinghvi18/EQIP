from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from random import Random

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.schemas import (
    Bug,
    BugStatus,
    DetectionStage,
    Project,
    QualityEvent,
    RootCauseCategory,
    RoleScore,
    SeverityLevel,
    Sprint,
    SprintStatus,
    Story,
    StoryStatus,
    User,
    UserRole,
)
from app.services.scoring_engine import recompute_role_scores, sync_bug_quality_events, sync_story_quality_events

RNG = Random(42)
MODULES = ["Auth", "Payment", "Dashboard", "Notifications", "Reports", "User Management", "Search", "API Gateway"]

USER_SEEDS = [
    ("Ava Grant", "ava.grant@eqip.dev", UserRole.ADMIN, "Platform Ops"),
    ("Mason Reed", "mason.reed@eqip.dev", UserRole.ENGINEERING_MANAGER, "Platform Ops"),
    ("Priya Shah", "priya.shah@eqip.dev", UserRole.ENGINEERING_MANAGER, "Delivery Excellence"),
    ("Noah Kim", "noah.kim@eqip.dev", UserRole.BUSINESS_ANALYST, "Portal"),
    ("Sophia Patel", "sophia.patel@eqip.dev", UserRole.BUSINESS_ANALYST, "Payments"),
    ("Liam Chen", "liam.chen@eqip.dev", UserRole.BUSINESS_ANALYST, "Operations"),
    ("Olivia Brooks", "olivia.brooks@eqip.dev", UserRole.DEVELOPER, "Portal"),
    ("Ethan Wright", "ethan.wright@eqip.dev", UserRole.DEVELOPER, "Payments"),
    ("Mia Alvarez", "mia.alvarez@eqip.dev", UserRole.DEVELOPER, "Core Services"),
    ("Lucas Hart", "lucas.hart@eqip.dev", UserRole.DEVELOPER, "Operations"),
    ("Emma Ross", "emma.ross@eqip.dev", UserRole.TESTER, "Portal QA"),
    ("James Foster", "james.foster@eqip.dev", UserRole.TESTER, "Payments QA"),
    ("Charlotte Green", "charlotte.green@eqip.dev", UserRole.TESTER, "Ops QA"),
    ("Benjamin Cole", "benjamin.cole@eqip.dev", UserRole.TESTER, "Core QA"),
    ("Amelia Stone", "amelia.stone@eqip.dev", UserRole.AUTOMATION_ENGINEER, "QE Automation"),
    ("Henry Mills", "henry.mills@eqip.dev", UserRole.AUTOMATION_ENGINEER, "QE Automation"),
]

PROJECT_SEEDS = [
    ("ORION", "Customer Portal Revamp", "Modernise portal journeys and account surfaces."),
    ("NOVA", "Payments Reliability Program", "Improve payments resilience, trust, and compliance."),
    ("PULSE", "Operations Intelligence Suite", "Analytics and back-office quality acceleration."),
]

SPRINT_SEEDS = [
    ("ORION Sprint 11", "Stabilise login and homepage journeys.", "ORION", date(2026, 4, 6), date(2026, 4, 19), "R11", SprintStatus.CLOSED),
    ("ORION Sprint 12", "Improve user engagement and notifications.", "ORION", date(2026, 4, 20), date(2026, 5, 3), "R12", SprintStatus.CLOSED),
    ("ORION Hardening", "Release hardening and support readiness.", "ORION", date(2026, 5, 4), date(2026, 5, 17), "R12.1", SprintStatus.CLOSED),
    ("NOVA Sprint 7", "Reduce payment failure modes.", "NOVA", date(2026, 5, 18), date(2026, 5, 31), "R7", SprintStatus.CLOSED),
    ("NOVA Sprint 8", "Strengthen gateway and search resilience.", "NOVA", date(2026, 6, 1), date(2026, 6, 14), "R8", SprintStatus.CLOSED),
    ("PULSE Sprint 5", "Improve operational visibility and reporting.", "PULSE", date(2026, 6, 15), date(2026, 6, 28), "R5", SprintStatus.CLOSED),
    ("PULSE Sprint 6", "Scale management and analytics workflows.", "PULSE", date(2026, 6, 29), date(2026, 7, 12), "R6", SprintStatus.ACTIVE),
]

STORY_TEMPLATES = {
    "Auth": [
        "Add password rotation policy enforcement",
        "Support step-up MFA during suspicious sign-in",
        "Expose session history for account security",
        "Refine SSO fallback and passwordless login controls",
    ],
    "Payment": [
        "Add partial capture support for card payments",
        "Harden payment retry orchestration",
        "Launch currency-aware refund workflow",
        "Support merchant dispute evidence uploads",
    ],
    "Dashboard": [
        "Improve executive quality summary cards",
        "Add trend comparison widget for releases",
        "Refine dashboard filters for modules and severity",
        "Optimise KPI refresh for large portfolios",
    ],
    "Notifications": [
        "Create delivery preference center",
        "Add release-quality alert digests",
        "Support multi-channel incident notifications",
        "Track notification retry and fallback history",
    ],
    "Reports": [
        "Export defect trend summaries to CSV",
        "Build module RCA summary report",
        "Support release quality scorecards",
        "Improve heavy report query caching",
    ],
    "User Management": [
        "Allow role reassignment with approval flow",
        "Expose quality coaching notes on profiles",
        "Add team-level permissions matrix",
        "Improve bulk user activation workflows",
    ],
    "Search": [
        "Add semantic filter presets for bug search",
        "Improve story lookup relevance and synonyms",
        "Support saved cross-project search views",
        "Speed up faceted search aggregation",
    ],
    "API Gateway": [
        "Add request signing for partner APIs",
        "Improve gateway timeout and retry rules",
        "Expose downstream health probe summary",
        "Track per-route throttling and audit headers",
    ],
}

BUG_BLUEPRINTS = {
    "Auth": [
        ("Blank password validation missing on alternate login flow", RootCauseCategory.VALIDATION, "Server-side validation missed for blank password edge case", SeverityLevel.HIGH, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.6, "Tester": 0.25, "Business Analyst": 0.15}),
        ("Password policy AC omitted special-character requirement", RootCauseCategory.ACCEPTANCE_CRITERIA_MISSING, "Acceptance criteria did not state the special-character rule", SeverityLevel.MEDIUM, DetectionStage.CODE_REVIEW, DetectionStage.REQUIREMENT, {"Business Analyst": 0.55, "Developer": 0.25, "Tester": 0.20}),
        ("Session refresh endpoint accepts expired token", RootCauseCategory.API, "Refresh token expiry branch skipped during implementation", SeverityLevel.HIGH, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.7, "Tester": 0.2, "Automation Engineer": 0.1}),
        ("Trusted-device MFA bypass", RootCauseCategory.SECURITY, "Cookie trust path lacked secondary validation", SeverityLevel.CRITICAL, DetectionStage.UAT, DetectionStage.DEVELOPMENT, {"Developer": 0.7, "Tester": 0.2, "Business Analyst": 0.1}),
        ("SSO fallback accepts whitespace-only password", RootCauseCategory.VALIDATION, "Legacy fallback path bypassed input sanitiser", SeverityLevel.PRODUCTION, DetectionStage.PRODUCTION, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.2, "Automation Engineer": 0.15}),
        ("Login regression suite missed disabled-account scenario", RootCauseCategory.TESTING_GAP, "Disabled-account path absent from manual and automated regression packs", SeverityLevel.HIGH, DetectionStage.PRODUCTION, DetectionStage.TESTING, {"Tester": 0.55, "Automation Engineer": 0.35, "Developer": 0.10}),
    ],
    "Payment": [
        ("Webhook replay signature not validated", RootCauseCategory.SECURITY, "Signature verification was skipped for retry path", SeverityLevel.SECURITY, DetectionStage.PRODUCTION, DetectionStage.DEVELOPMENT, {"Developer": 0.7, "Tester": 0.15, "Automation Engineer": 0.15}),
        ("Card PAN masking omitted in retry logs", RootCauseCategory.SECURITY, "Sensitive fields were logged in an exception handler", SeverityLevel.CRITICAL, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.75, "Tester": 0.15, "Business Analyst": 0.10}),
        ("Refund flow ignores idempotency token", RootCauseCategory.API, "API contract was implemented without idempotency persistence", SeverityLevel.HIGH, DetectionStage.UAT, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.20, "Business Analyst": 0.15}),
        ("Settlement ledger rounds micro-amounts incorrectly", RootCauseCategory.DATABASE, "Database precision rule differed from business rounding spec", SeverityLevel.HIGH, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.5, "Business Analyst": 0.3, "Tester": 0.2}),
        ("Multi-currency fallback rule unclear", RootCauseCategory.REQUIREMENT_GAP, "Requirement text omitted fallback order for unsupported currency pairs", SeverityLevel.MEDIUM, DetectionStage.TESTING, DetectionStage.REQUIREMENT, {"Business Analyst": 0.6, "Developer": 0.25, "Tester": 0.15}),
        ("Payment polling saturates gateway under spike traffic", RootCauseCategory.PERFORMANCE, "Polling strategy lacked backoff and cache awareness", SeverityLevel.PERFORMANCE, DetectionStage.RELEASE, DetectionStage.DEVELOPMENT, {"Developer": 0.6, "Automation Engineer": 0.2, "Tester": 0.2}),
    ],
    "Dashboard": [
        ("Executive cards overlap on tablet viewport", RootCauseCategory.UI, "Responsive breakpoint did not account for extra KPI card", SeverityLevel.GENERAL, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.55, "Tester": 0.35, "Business Analyst": 0.10}),
        ("Trend widget compares wrong release label", RootCauseCategory.BUSINESS_LOGIC, "Release selector used stale release mapping", SeverityLevel.MEDIUM, DetectionStage.CODE_REVIEW, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.20, "Business Analyst": 0.15}),
        ("Heatmap uses inconsistent module casing", RootCauseCategory.UI, "Normalization rule missing in transformation layer", SeverityLevel.COSMETIC, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.5, "Tester": 0.3, "Automation Engineer": 0.2}),
        ("KPI refresh blocks when portfolio exceeds 500 stories", RootCauseCategory.PERFORMANCE, "Expensive aggregation query lacked pagination safeguards", SeverityLevel.HIGH, DetectionStage.UAT, DetectionStage.DEVELOPMENT, {"Developer": 0.7, "Automation Engineer": 0.2, "Tester": 0.1}),
        ("Release score delta excludes zero-bug stories", RootCauseCategory.BUSINESS_LOGIC, "Scorecard formula dropped zero-defect bonus branch", SeverityLevel.MEDIUM, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Business Analyst": 0.2, "Tester": 0.15}),
        ("Dashboard snapshot stale after deploy", RootCauseCategory.DEPLOYMENT, "Cache bust hook missing in deployment pipeline", SeverityLevel.GENERAL, DetectionStage.RELEASE, DetectionStage.RELEASE, {"Automation Engineer": 0.6, "Developer": 0.25, "Tester": 0.15}),
    ],
    "Notifications": [
        ("Digest email template drops release name", RootCauseCategory.UI, "Template variable not mapped after content update", SeverityLevel.GENERAL, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.55, "Tester": 0.30, "Business Analyst": 0.15}),
        ("Slack alerts duplicate after retry", RootCauseCategory.API, "Idempotency token not carried across retry path", SeverityLevel.MEDIUM, DetectionStage.UAT, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.2, "Automation Engineer": 0.15}),
        ("SMS provider timeout handled as success", RootCauseCategory.BUSINESS_LOGIC, "Fallback state machine treated timeout as delivered", SeverityLevel.HIGH, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.25, "Business Analyst": 0.10}),
        ("Alert routing misses quiet-hours override", RootCauseCategory.REQUIREMENT_GAP, "Requirement omitted manager override behavior", SeverityLevel.MEDIUM, DetectionStage.CODE_REVIEW, DetectionStage.REQUIREMENT, {"Business Analyst": 0.55, "Developer": 0.25, "Tester": 0.20}),
        ("Webhook retry queue stalls in staging", RootCauseCategory.ENVIRONMENT, "Queue worker secret rotated only in staging environment", SeverityLevel.GENERAL, DetectionStage.RELEASE, DetectionStage.RELEASE, {"Automation Engineer": 0.6, "Developer": 0.2, "Tester": 0.2}),
        ("Notification history misses attachment metadata", RootCauseCategory.API, "Serialization layer dropped nested attachment payload", SeverityLevel.MEDIUM, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.7, "Tester": 0.2, "Automation Engineer": 0.1}),
    ],
    "Reports": [
        ("CSV export duplicates header row", RootCauseCategory.UI, "Export formatter appended header for each chunk", SeverityLevel.COSMETIC, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.45, "Tester": 0.4, "Automation Engineer": 0.15}),
        ("RCA report totals drift from dashboard totals", RootCauseCategory.BUSINESS_LOGIC, "Summary report used release scope instead of sprint scope", SeverityLevel.MEDIUM, DetectionStage.CODE_REVIEW, DetectionStage.DEVELOPMENT, {"Developer": 0.6, "Business Analyst": 0.25, "Tester": 0.15}),
        ("Heavy report query triggers lock contention", RootCauseCategory.DATABASE, "Missing covering index on report snapshot table", SeverityLevel.HIGH, DetectionStage.UAT, DetectionStage.DEVELOPMENT, {"Developer": 0.7, "Automation Engineer": 0.15, "Tester": 0.15}),
        ("Scheduled report email sent before attachment upload", RootCauseCategory.REGRESSION, "Async sequencing changed during queue refactor", SeverityLevel.MEDIUM, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.25, "Automation Engineer": 0.10}),
        ("Module filter omitted from release scorecard", RootCauseCategory.ACCEPTANCE_CRITERIA_MISSING, "Acceptance criteria did not call out filtered export behavior", SeverityLevel.GENERAL, DetectionStage.TESTING, DetectionStage.REQUIREMENT, {"Business Analyst": 0.5, "Developer": 0.3, "Tester": 0.2}),
        ("Nightly report refresh fails after schema patch", RootCauseCategory.DEPLOYMENT, "Migration sequence missed materialized-view rebuild", SeverityLevel.HIGH, DetectionStage.RELEASE, DetectionStage.RELEASE, {"Automation Engineer": 0.65, "Developer": 0.2, "Tester": 0.15}),
    ],
    "User Management": [
        ("Role reassignment bypasses secondary approval", RootCauseCategory.SECURITY, "Approval guard skipped for bulk reassignment path", SeverityLevel.CRITICAL, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.2, "Business Analyst": 0.15}),
        ("Bulk activation skips suspended users rule", RootCauseCategory.VALIDATION, "Validation rule missing on batch service", SeverityLevel.HIGH, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.6, "Tester": 0.25, "Business Analyst": 0.15}),
        ("Profile coaching notes truncate markdown", RootCauseCategory.UI, "Renderer sanitiser strips headings unexpectedly", SeverityLevel.GENERAL, DetectionStage.UAT, DetectionStage.DEVELOPMENT, {"Developer": 0.55, "Tester": 0.3, "Business Analyst": 0.15}),
        ("Permissions matrix lacks contractor role", RootCauseCategory.REQUIREMENT_GAP, "Requirement set did not include contractor persona", SeverityLevel.MEDIUM, DetectionStage.CODE_REVIEW, DetectionStage.REQUIREMENT, {"Business Analyst": 0.6, "Developer": 0.25, "Tester": 0.15}),
        ("Activation email sent to deprovisioned alias", RootCauseCategory.VALIDATION, "Historical alias mapping not validated before send", SeverityLevel.DATA_LOSS, DetectionStage.PRODUCTION, DetectionStage.DEVELOPMENT, {"Developer": 0.55, "Tester": 0.25, "Automation Engineer": 0.20}),
        ("Team filter omits archived squad members", RootCauseCategory.REGRESSION, "Refactor dropped archived-user toggle from query", SeverityLevel.MEDIUM, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.6, "Tester": 0.25, "Automation Engineer": 0.15}),
    ],
    "Search": [
        ("Semantic presets ignore severity filter", RootCauseCategory.API, "Search API failed to propagate severity facet", SeverityLevel.MEDIUM, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.6, "Tester": 0.25, "Business Analyst": 0.15}),
        ("Saved search opens wrong default workspace", RootCauseCategory.BUSINESS_LOGIC, "Workspace preference precedence order changed", SeverityLevel.GENERAL, DetectionStage.CODE_REVIEW, DetectionStage.DEVELOPMENT, {"Developer": 0.55, "Tester": 0.2, "Business Analyst": 0.25}),
        ("Facet aggregation slows to 9s on large datasets", RootCauseCategory.PERFORMANCE, "Search aggregation lacked precomputed counters", SeverityLevel.PERFORMANCE, DetectionStage.UAT, DetectionStage.DEVELOPMENT, {"Developer": 0.7, "Automation Engineer": 0.15, "Tester": 0.15}),
        ("Synonym expansion misses acronym forms", RootCauseCategory.ACCEPTANCE_CRITERIA_MISSING, "Acceptance criteria did not define acronym synonym coverage", SeverityLevel.MEDIUM, DetectionStage.TESTING, DetectionStage.REQUIREMENT, {"Business Analyst": 0.5, "Developer": 0.3, "Tester": 0.2}),
        ("Vector refresh job stalls after deploy", RootCauseCategory.DEPLOYMENT, "Deployment job skipped queue warm-up step", SeverityLevel.GENERAL, DetectionStage.RELEASE, DetectionStage.RELEASE, {"Automation Engineer": 0.6, "Developer": 0.25, "Tester": 0.15}),
        ("Saved view import accepts malformed filter JSON", RootCauseCategory.VALIDATION, "API payload validation absent for imported filters", SeverityLevel.HIGH, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.6, "Tester": 0.25, "Automation Engineer": 0.15}),
    ],
    "API Gateway": [
        ("Request signing skips canonical path normalization", RootCauseCategory.SECURITY, "Signer omitted canonicalization for encoded paths", SeverityLevel.SECURITY, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.7, "Tester": 0.15, "Automation Engineer": 0.15}),
        ("Gateway retries non-idempotent POST requests", RootCauseCategory.API, "Retry policy applied generic rule to unsafe method", SeverityLevel.HIGH, DetectionStage.UAT, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.2, "Business Analyst": 0.15}),
        ("Health summary caches stale downstream state", RootCauseCategory.PERFORMANCE, "Probe cache TTL too high for degraded systems", SeverityLevel.MEDIUM, DetectionStage.RELEASE, DetectionStage.DEVELOPMENT, {"Developer": 0.55, "Automation Engineer": 0.3, "Tester": 0.15}),
        ("Audit header omitted for partner traffic", RootCauseCategory.REGRESSION, "Routing middleware refactor dropped audit header branch", SeverityLevel.HIGH, DetectionStage.TESTING, DetectionStage.DEVELOPMENT, {"Developer": 0.65, "Tester": 0.2, "Automation Engineer": 0.15}),
        ("Rate limiter does not honour premium burst rule", RootCauseCategory.REQUIREMENT_GAP, "Business rule for premium burst traffic was not documented", SeverityLevel.MEDIUM, DetectionStage.CODE_REVIEW, DetectionStage.REQUIREMENT, {"Business Analyst": 0.55, "Developer": 0.25, "Tester": 0.20}),
        ("Gateway deploy misses WAF policy sync", RootCauseCategory.DEPLOYMENT, "Release script skipped WAF policy promotion step", SeverityLevel.CRITICAL, DetectionStage.RELEASE, DetectionStage.RELEASE, {"Automation Engineer": 0.65, "Developer": 0.2, "Tester": 0.15}),
    ],
}

MODULE_PROJECT = {
    "Auth": "ORION",
    "Dashboard": "ORION",
    "Notifications": "ORION",
    "Payment": "NOVA",
    "Search": "NOVA",
    "API Gateway": "NOVA",
    "Reports": "PULSE",
    "User Management": "PULSE",
}

MODULE_SPRINTS = {
    "Auth": ["ORION Sprint 11", "ORION Sprint 12", "ORION Hardening"],
    "Dashboard": ["ORION Sprint 11", "ORION Sprint 12", "ORION Hardening"],
    "Notifications": ["ORION Sprint 12", "ORION Hardening"],
    "Payment": ["NOVA Sprint 7", "NOVA Sprint 8"],
    "Search": ["NOVA Sprint 8"],
    "API Gateway": ["NOVA Sprint 8"],
    "Reports": ["PULSE Sprint 5", "PULSE Sprint 6"],
    "User Management": ["PULSE Sprint 5", "PULSE Sprint 6"],
}


def _dt(target_date: date, days: int = 0, hour: int = 10) -> datetime:
    return datetime.combine(target_date + timedelta(days=days), time(hour=hour), tzinfo=timezone.utc)


def _user_map(db: Session) -> dict[str, User]:
    return {user.email: user for user in db.scalars(select(User)).all()}


def _pick(users: dict[str, User], role: UserRole, index: int) -> User:
    candidates = [user for user in users.values() if user.role == role]
    return candidates[index % len(candidates)]


def _detector_for_stage(story: Story, stage: DetectionStage) -> int | None:
    if stage == DetectionStage.REQUIREMENT:
        return story.ba_id
    if stage in {DetectionStage.DEVELOPMENT, DetectionStage.CODE_REVIEW}:
        return story.reviewer_id or story.developer_id
    if stage in {DetectionStage.TESTING, DetectionStage.UAT, DetectionStage.PRODUCTION}:
        return story.tester_id
    if stage in {DetectionStage.AUTOMATION, DetectionStage.RELEASE}:
        return story.automation_id or story.tester_id
    return story.tester_id


def _assignee_for_category(story: Story, category: RootCauseCategory) -> int | None:
    if category in {RootCauseCategory.DEPLOYMENT, RootCauseCategory.AUTOMATION_GAP, RootCauseCategory.ENVIRONMENT}:
        return story.automation_id or story.developer_id
    return story.developer_id or story.automation_id


def seed_demo_data(db: Session) -> None:
    has_projects = db.scalar(select(Project.id).limit(1)) is not None
    if has_projects and not settings.reset_demo_data:
        return
    if has_projects and settings.reset_demo_data:
        for model in (RoleScore, QualityEvent, Bug, Story, Sprint, Project, User):
            db.query(model).delete()
        db.commit()

    users = []
    for full_name, email, role, team in USER_SEEDS:
        users.append(User(full_name=full_name, email=email, role=role, team=team, avatar_url=f"https://api.dicebear.com/9.x/initials/svg?seed={full_name.replace(' ', '%20')}"))
    db.add_all(users)
    db.flush()
    user_lookup = _user_map(db)

    projects = []
    for key, name, description in PROJECT_SEEDS:
        projects.append(Project(key=key, name=name, description=description, status="Active"))
    db.add_all(projects)
    db.flush()
    project_lookup = {project.key: project for project in projects}

    sprints = []
    for name, goal, project_key, start_date, end_date, release_name, status in SPRINT_SEEDS:
        sprints.append(
            Sprint(
                name=name,
                goal=goal,
                project_id=project_lookup[project_key].id,
                start_date=start_date,
                end_date=end_date,
                release_name=release_name,
                status=status,
            )
        )
    db.add_all(sprints)
    db.flush()
    sprint_lookup = {sprint.name: sprint for sprint in sprints}

    stories = []
    project_story_counter = defaultdict(int)
    ba_index = dev_index = test_index = auto_index = 0
    for module in MODULES:
        for title_index, title in enumerate(STORY_TEMPLATES[module]):
            project_key = MODULE_PROJECT[module]
            candidate_sprints = [sprint_lookup[name] for name in MODULE_SPRINTS[module]]
            sprint = candidate_sprints[title_index % len(candidate_sprints)]
            project_story_counter[project_key] += 1
            story_number = 100 + project_story_counter[project_key]
            ba = _pick(user_lookup, UserRole.BUSINESS_ANALYST, ba_index)
            developer = _pick(user_lookup, UserRole.DEVELOPER, dev_index)
            tester = _pick(user_lookup, UserRole.TESTER, test_index)
            automation = _pick(user_lookup, UserRole.AUTOMATION_ENGINEER, auto_index)
            reviewer = _pick(user_lookup, UserRole.DEVELOPER, dev_index + 1)
            ba_index += 1
            dev_index += 1
            test_index += 1
            auto_index += 1
            estimated = sprint.end_date - timedelta(days=2)
            completion = estimated - timedelta(days=RNG.choice([0, 1]))
            stories.append(
                Story(
                    story_key=f"{project_key}-{story_number}",
                    title=title,
                    epic=f"{module} Quality Foundations",
                    project_id=project_lookup[project_key].id,
                    sprint_id=sprint.id,
                    module=module,
                    priority=RNG.choice(["P1", "P1", "P2"]),
                    complexity=RNG.choice(["Medium", "High", "Medium", "Low"]),
                    story_points=RNG.choice([3, 5, 8]),
                    acceptance_criteria=f"{title}. Acceptance criteria cover happy path, edge cases, auditability, and release readiness.",
                    ba_id=ba.id,
                    developer_id=developer.id,
                    tester_id=tester.id,
                    automation_id=automation.id,
                    reviewer_id=reviewer.id,
                    status=StoryStatus.DONE if sprint.status == SprintStatus.CLOSED else StoryStatus.TESTING,
                    estimated_date=estimated,
                    completion_date=completion if sprint.status == SprintStatus.CLOSED else None,
                    release_name=sprint.release_name,
                    environment=RNG.choice(["QA", "Staging", "Production Mirror"]),
                    attachments=[{"type": "figma", "label": f"{module} design review"}],
                    documentation=f"Implementation notes for {title.lower()} with validation, telemetry, and release checklist.",
                )
            )
    db.add_all(stories)
    db.flush()

    module_story_map = defaultdict(list)
    for story in stories:
        module_story_map[story.module].append(story)

    em_user = next(user for user in users if user.role == UserRole.ENGINEERING_MANAGER)
    bugs = []
    project_bug_counter = defaultdict(int)
    for module, blueprints in BUG_BLUEPRINTS.items():
        story_pool = module_story_map[module]
        for index, blueprint in enumerate(blueprints):
            summary, category, root_cause, severity, detected_stage, origin_stage, ownership_split = blueprint
            story = story_pool[index % len(story_pool)]
            project = story.project
            sprint = story.sprint
            project_bug_counter[project.key] += 1
            bug_number = 400 + project_bug_counter[project.key]
            created_at = _dt(sprint.start_date, days=1 + (index % 5), hour=9 + (index % 4))
            closed_at = created_at + timedelta(days=2 + (index % 4))
            bugs.append(
                Bug(
                    bug_key=f"{project.key}-BUG-{bug_number}",
                    story_id=story.id,
                    project_id=project.id,
                    sprint_id=sprint.id,
                    module=module,
                    summary=summary,
                    description=f"{summary}. RCA note: {root_cause}. The issue was traced during {detected_stage.value.lower()}.",
                    severity=severity,
                    priority="P0" if severity in {SeverityLevel.CRITICAL, SeverityLevel.PRODUCTION, SeverityLevel.SECURITY, SeverityLevel.DATA_LOSS} else "P1",
                    environment="Production" if detected_stage == DetectionStage.PRODUCTION else "Staging",
                    detected_by_id=_detector_for_stage(story, detected_stage),
                    detected_stage=detected_stage,
                    assigned_to_id=_assignee_for_category(story, category),
                    root_cause=root_cause,
                    root_cause_category=category,
                    origin_stage=origin_stage,
                    ownership_split=ownership_split,
                    bug_category=category.value,
                    resolution=f"Implemented fix, tests, and monitoring for {summary.lower()}.",
                    status=BugStatus.CLOSED,
                    created_date=created_at,
                    closed_date=closed_at,
                    ai_suggested={
                        "root_cause": root_cause,
                        "origin_stage": origin_stage.value,
                        "ownership_split": ownership_split,
                        "severity": severity.value,
                    },
                    ai_confidence=round(RNG.uniform(0.78, 0.96), 2),
                    human_approved_by_id=em_user.id,
                    human_approved_at=created_at + timedelta(hours=6),
                )
            )
    db.add_all(bugs)
    db.commit()

    stories = list(db.scalars(select(Story).options(selectinload(Story.project), selectinload(Story.sprint), selectinload(Story.bugs))).all())
    bugs = list(db.scalars(select(Bug).options(selectinload(Bug.story), selectinload(Bug.detected_by), selectinload(Bug.assigned_to))).all())
    for story in stories:
        sync_story_quality_events(db, story)
    for bug in bugs:
        sync_bug_quality_events(db, bug)
    db.commit()
    recompute_role_scores(db, period="all-time")
