"""AI Reasoning Service (Phase 2) - Root cause, owner, severity suggestions.

Design principles (from EQIP Design Spec §7):
- AI suggests, humans decide
- Proposes root cause + category, origin stage/owner, severity, confidence
- No AI suggestion affects a score/rank/badge until EM approves (FR-9)
- Uses open-weight models via OpenAI-compatible API
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import (
    Bug,
    CoachingRecommendation,
    QualityEvent,
    RootCauseCategory,
    OriginStage,
    BugSeverity,
    Story,
    UserRole,
)


# Root cause keyword mapping for rule-based suggestions
ROOT_CAUSE_KEYWORDS = {
    RootCauseCategory.REQUIREMENT_GAP: [
        "requirement", "spec", "specification", "missing requirement",
        "not specified", "unclear requirement", "ambiguous",
    ],
    RootCauseCategory.ACCEPTANCE_CRITERIA_MISSING: [
        "acceptance criteria", "ac missing", "no criteria", "undefined behavior",
    ],
    RootCauseCategory.BUSINESS_LOGIC: [
        "logic", "business rule", "calculation", "workflow", "process",
    ],
    RootCauseCategory.VALIDATION: [
        "validation", "input", "check", "verify", "constraint",
        "boundary", "null", "empty", "format",
    ],
    RootCauseCategory.UI: [
        "ui", "display", "layout", "css", "visual", "rendering", "button",
        "label", "alignment", "responsive",
    ],
    RootCauseCategory.API: [
        "api", "endpoint", "request", "response", "status code",
        "timeout", "payload", "rest",
    ],
    RootCauseCategory.DATABASE: [
        "database", "db", "query", "sql", "migration", "schema",
        "index", "deadlock", "constraint",
    ],
    RootCauseCategory.SECURITY: [
        "security", "auth", "authentication", "authorization", "xss",
        "injection", "csrf", "token", "permission",
    ],
    RootCauseCategory.PERFORMANCE: [
        "performance", "slow", "timeout", "memory", "cpu", "load",
        "latency", "optimization",
    ],
    RootCauseCategory.REGRESSION: [
        "regression", "broke", "worked before", "introduced by",
        "after change", "after update",
    ],
}

# Origin stage inference based on root cause
ORIGIN_STAGE_MAP = {
    RootCauseCategory.REQUIREMENT_GAP: OriginStage.REQUIREMENT,
    RootCauseCategory.ACCEPTANCE_CRITERIA_MISSING: OriginStage.REQUIREMENT,
    RootCauseCategory.BUSINESS_LOGIC: OriginStage.DEVELOPMENT,
    RootCauseCategory.VALIDATION: OriginStage.DEVELOPMENT,
    RootCauseCategory.UI: OriginStage.DEVELOPMENT,
    RootCauseCategory.API: OriginStage.DEVELOPMENT,
    RootCauseCategory.DATABASE: OriginStage.DEVELOPMENT,
    RootCauseCategory.SECURITY: OriginStage.DEVELOPMENT,
    RootCauseCategory.PERFORMANCE: OriginStage.DEVELOPMENT,
    RootCauseCategory.REGRESSION: OriginStage.TESTING,
    RootCauseCategory.TESTING_GAP: OriginStage.TESTING,
    RootCauseCategory.AUTOMATION_GAP: OriginStage.AUTOMATION,
    RootCauseCategory.DEPLOYMENT: OriginStage.RELEASE,
    RootCauseCategory.ENVIRONMENT: OriginStage.RELEASE,
}


def suggest_root_cause(bug: Bug) -> dict:
    """Suggest root cause, origin stage, severity, and ownership split for a bug.

    Returns AI suggestion dict with confidence score.
    Uses keyword-based analysis (rule engine) as the default;
    in production, this would call an LLM via OpenAI-compatible API.
    """
    text = f"{bug.summary} {bug.description or ''}".lower()

    # Find best matching root cause category
    best_category = RootCauseCategory.UNKNOWN
    best_score = 0.0

    for category, keywords in ROOT_CAUSE_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text)
        score = matches / len(keywords) if keywords else 0
        if score > best_score:
            best_score = score
            best_category = category

    # Determine confidence based on keyword match strength
    confidence = min(best_score * 2.5, 0.95) if best_score > 0 else 0.1

    # Determine origin stage
    origin_stage = ORIGIN_STAGE_MAP.get(best_category, OriginStage.DEVELOPMENT)

    # Suggest ownership split based on origin
    ownership_split = _suggest_ownership(origin_stage, best_category)

    # Suggest severity based on keywords
    suggested_severity = _suggest_severity(text, bug.severity)

    return {
        "root_cause_category": best_category.value,
        "origin_stage": origin_stage.value,
        "severity": suggested_severity.value,
        "ownership_split": ownership_split,
        "confidence": round(confidence, 2),
        "reasoning": f"Based on keyword analysis: detected '{best_category.value}' "
                     f"pattern with {round(confidence * 100)}% confidence. "
                     f"Origin mapped to '{origin_stage.value}' stage.",
    }


def _suggest_ownership(
    origin_stage: OriginStage, category: RootCauseCategory
) -> dict:
    """Suggest ownership split based on origin stage and category."""
    if origin_stage == OriginStage.REQUIREMENT:
        return {"business_analyst": 60, "developer": 20, "tester": 20}
    elif origin_stage == OriginStage.DEVELOPMENT:
        return {"developer": 70, "tester": 30}
    elif origin_stage == OriginStage.TESTING:
        return {"tester": 60, "developer": 30, "business_analyst": 10}
    elif origin_stage == OriginStage.AUTOMATION:
        return {"automation_engineer": 70, "tester": 30}
    else:
        return {"developer": 50, "tester": 30, "business_analyst": 20}


def _suggest_severity(text: str, current_severity: BugSeverity) -> BugSeverity:
    """Suggest severity based on text analysis."""
    critical_keywords = ["crash", "data loss", "security breach", "production down"]
    high_keywords = ["blocking", "cannot proceed", "major", "critical path"]
    medium_keywords = ["incorrect", "wrong", "broken"]

    for kw in critical_keywords:
        if kw in text:
            return BugSeverity.CRITICAL
    for kw in high_keywords:
        if kw in text:
            return BugSeverity.HIGH
    for kw in medium_keywords:
        if kw in text:
            return BugSeverity.MEDIUM

    return current_severity


def generate_coaching_recommendations(
    db: Session, user_id: int, period: str
) -> list[CoachingRecommendation]:
    """Generate coaching recommendations based on quality event patterns (FR-15).

    Analyzes the user's quality events to find patterns and generate
    specific, actionable coaching tips.
    """
    events = (
        db.query(QualityEvent)
        .filter(QualityEvent.actor_id == user_id)
        .order_by(QualityEvent.created_at.desc())
        .limit(50)
        .all()
    )

    if not events:
        return []

    # Analyze patterns
    negative_events = [e for e in events if e.delta < 0]
    positive_events = [e for e in events if e.delta > 0]

    # Group negative events by type
    negative_by_type: dict[str, int] = {}
    for e in negative_events:
        key = e.event_type.value
        negative_by_type[key] = negative_by_type.get(key, 0) + 1

    recommendations = []

    # Generate recommendations for frequent issues
    for event_type, count in sorted(negative_by_type.items(), key=lambda x: -x[1]):
        if count >= 2:
            rec = _create_recommendation(db, user_id, event_type, count, period)
            if rec:
                recommendations.append(rec)

    # Positive reinforcement
    if positive_events and len(positive_events) > len(negative_events):
        rec = CoachingRecommendation(
            user_id=user_id,
            category="positive_trend",
            recommendation=(
                f"Great work! You have {len(positive_events)} positive quality events "
                f"vs {len(negative_events)} areas for improvement. Keep maintaining this standard."
            ),
            supporting_data={"positive_count": len(positive_events), "negative_count": len(negative_events)},
        )
        db.add(rec)
        recommendations.append(rec)

    if recommendations:
        db.commit()

    return recommendations


def _create_recommendation(
    db: Session, user_id: int, event_type: str, count: int, period: str
) -> Optional[CoachingRecommendation]:
    """Create a specific coaching recommendation based on event patterns."""
    coaching_map = {
        "validation_bug": (
            "validation",
            f"Validation bugs appeared {count} times. Consider adding a validation "
            "checklist to your code review process and writing unit tests for all "
            "input boundaries before implementation.",
        ),
        "logic_bug": (
            "business_logic",
            f"Logic bugs occurred {count} times. Review acceptance criteria more carefully "
            "before coding. Consider pair-programming on complex business rules.",
        ),
        "failed_code_review": (
            "code_quality",
            f"Code reviews failed {count} times. Study the common feedback patterns "
            "and create a personal pre-review checklist.",
        ),
        "production_defect": (
            "production_quality",
            f"Production defects found {count} times. Strengthen integration testing "
            "and consider adding more edge-case coverage.",
        ),
        "escaped_production_defect": (
            "testing_coverage",
            f"Escaped defects detected {count} times. Review test coverage for the "
            "affected modules and add regression tests.",
        ),
        "requirement_gap_traced": (
            "requirements",
            f"Requirement gaps found {count} times. Consider using structured templates "
            "for acceptance criteria and scheduling early walkthroughs.",
        ),
        "flaky_tests": (
            "automation_stability",
            f"Flaky tests reported {count} times. Invest in test isolation, "
            "remove timing dependencies, and add retry mechanisms.",
        ),
    }

    if event_type in coaching_map:
        category, recommendation = coaching_map[event_type]
        rec = CoachingRecommendation(
            user_id=user_id,
            category=category,
            recommendation=recommendation,
            supporting_data={"event_type": event_type, "count": count, "period": period},
        )
        db.add(rec)
        return rec
    return None
