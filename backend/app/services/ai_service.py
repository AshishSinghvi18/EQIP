"""AI Reasoning Service (Phase 2) - Root cause, owner, severity suggestions.

Design principles (from EQIP Design Spec §7):
- AI suggests, humans decide
- Proposes root cause + category, origin stage/owner, severity, confidence
- No AI suggestion affects a score/rank/badge until EM approves (FR-9)
- Uses open-weight models via OpenAI-compatible API (Qwen3/DeepSeek V4)
- Falls back to rule-based keyword analysis when LLM is unavailable
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import (
    Bug,
    BugReasoningClass,
    CoachingRecommendation,
    QualityEvent,
    RootCauseCategory,
    OriginStage,
    BugSeverity,
    Story,
    UserRole,
)

logger = logging.getLogger(__name__)


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


def suggest_root_cause(bug: Bug, story: Optional[Story] = None) -> dict:
    """Suggest root cause, origin stage, severity, and ownership split for a bug.

    Returns AI suggestion dict with confidence score.
    Tries LLM-based analysis first; falls back to keyword-based rule engine.
    """
    # Try LLM-based suggestion first
    llm_result = _llm_suggest_root_cause(bug, story)
    if llm_result:
        return llm_result

    # Fall back to keyword-based analysis
    return _keyword_suggest_root_cause(bug)


def _llm_suggest_root_cause(bug: Bug, story: Optional[Story] = None) -> Optional[dict]:
    """Use LLM (OpenAI-compatible API) to suggest root cause analysis.

    Uses open-weight models (Qwen3, DeepSeek V4) via configurable API endpoint.
    """
    try:
        from openai import OpenAI

        if not settings.LLM_API_KEY and settings.LLM_API_BASE_URL == "http://localhost:11434/v1":
            client = OpenAI(
                base_url=settings.LLM_API_BASE_URL,
                api_key="not-needed",
                timeout=settings.LLM_TIMEOUT,
            )
        elif settings.LLM_API_KEY:
            client = OpenAI(
                base_url=settings.LLM_API_BASE_URL,
                api_key=settings.LLM_API_KEY,
                timeout=settings.LLM_TIMEOUT,
            )
        else:
            return None
    except Exception as e:
        logger.warning(f"LLM client creation failed: {e}")
        return None

    # Build context
    story_context = ""
    if story:
        story_context = (
            f"\nRelated Story: {story.title}\n"
            f"Acceptance Criteria: {story.acceptance_criteria or 'Not specified'}\n"
            f"Module: {story.module or 'Unknown'}\n"
        )

    categories = ", ".join(c.value for c in RootCauseCategory)
    stages = ", ".join(s.value for s in OriginStage)
    severities = ", ".join(s.value for s in BugSeverity)

    prompt = f"""Analyze this software bug and suggest its root cause classification.

Bug ID: {bug.bug_id}
Summary: {bug.summary}
Description: {bug.description or 'No description provided'}
Current Severity: {bug.severity.value}
Detected Stage: {bug.detected_stage.value if bug.detected_stage else 'Unknown'}
{story_context}

Classify using these categories:
- Root Cause Categories: {categories}
- Origin Stages: {stages}
- Severity Levels: {severities}

Respond in this exact format (one item per line):
ROOT_CAUSE_CATEGORY: [one category from the list]
ORIGIN_STAGE: [one stage from the list]
SEVERITY: [one severity from the list]
OWNERSHIP: [role:percentage pairs summing to 100, e.g. developer:70,tester:30]
CONFIDENCE: [0.0 to 1.0]
REASONING: [1-2 sentence explanation]"""

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a software quality analyst. Classify bugs by their root cause, "
                        "origin stage in the delivery chain, and severity. Be precise and concise."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )

        result_text = response.choices[0].message.content
        return _parse_llm_suggestion(result_text, bug)
    except Exception as e:
        logger.warning(f"LLM suggestion failed: {e}")
        return None


def _parse_llm_suggestion(text: str, bug: Bug) -> Optional[dict]:
    """Parse structured LLM response into suggestion dict."""
    try:
        parsed = {}
        for line in text.strip().split("\n"):
            line = line.strip()
            if line.startswith("ROOT_CAUSE_CATEGORY:"):
                parsed["category"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("ORIGIN_STAGE:"):
                parsed["origin"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("SEVERITY:"):
                parsed["severity"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("OWNERSHIP:"):
                ownership_str = line.split(":", 1)[1].strip()
                parsed["ownership"] = _parse_ownership_str(ownership_str)
            elif line.startswith("CONFIDENCE:"):
                try:
                    parsed["confidence"] = float(line.split(":", 1)[1].strip())
                except ValueError:
                    parsed["confidence"] = 0.5
            elif line.startswith("REASONING:"):
                parsed["reasoning"] = line.split(":", 1)[1].strip()

        if "category" not in parsed:
            return None

        # Validate and map to enums
        category_map = {c.value: c for c in RootCauseCategory}
        stage_map = {s.value: s for s in OriginStage}
        severity_map = {s.value: s for s in BugSeverity}

        category = category_map.get(parsed.get("category", ""), RootCauseCategory.UNKNOWN)
        origin = stage_map.get(parsed.get("origin", ""), OriginStage.DEVELOPMENT)
        severity = severity_map.get(parsed.get("severity", ""), bug.severity)

        return {
            "root_cause_category": category.value,
            "origin_stage": origin.value,
            "severity": severity.value,
            "ownership_split": parsed.get("ownership", {"developer": 70, "tester": 30}),
            "confidence": min(max(parsed.get("confidence", 0.5), 0.0), 1.0),
            "reasoning": parsed.get("reasoning", "LLM-based analysis"),
            "method": "llm",
            "model": settings.LLM_MODEL_NAME,
        }
    except Exception as e:
        logger.warning(f"Failed to parse LLM suggestion: {e}")
        return None


def _parse_ownership_str(ownership_str: str) -> dict:
    """Parse ownership string like 'developer:70,tester:30'."""
    ownership = {}
    for pair in ownership_str.split(","):
        parts = pair.strip().split(":")
        if len(parts) == 2:
            try:
                ownership[parts[0].strip()] = int(parts[1].strip())
            except ValueError:
                pass
    return ownership if ownership else {"developer": 70, "tester": 30}


def _keyword_suggest_root_cause(bug: Bug) -> dict:
    """Keyword-based root cause suggestion (rule engine fallback)."""
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
        "method": "keyword_rules",
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


# --- Bug-Reasoning Classification (v1.1, §7.4) ---

# Keyword patterns for reasoning class inference
REASONING_CLASS_KEYWORDS = {
    BugReasoningClass.SILLY_MISS: [
        "typo", "obvious", "careless", "oversight", "simple mistake",
        "forgot", "missed obvious", "trivial", "copy paste", "null check",
    ],
    BugReasoningClass.CRITICAL_MISS: [
        "security", "data loss", "critical", "core logic", "fundamental",
        "architecture", "design flaw", "race condition", "injection",
        "authentication", "authorization", "encryption",
    ],
    BugReasoningClass.INFO_NOT_IN_STORY: [
        "not specified", "unclear", "missing requirement", "ambiguous",
        "not mentioned", "not documented", "no acceptance criteria",
        "not in story", "missing info", "undocumented",
    ],
    BugReasoningClass.MISSING_UNIT_TEST: [
        "no unit test", "missing test", "untested", "no coverage",
        "test missing", "not tested", "unit test", "test coverage",
    ],
    BugReasoningClass.WRONG_TEST_CASES: [
        "wrong test", "incorrect test", "bad test case", "test case wrong",
        "missed scenario", "incomplete test", "test gap", "missing scenario",
    ],
}


def suggest_bug_reasoning_class(bug: Bug, story: Optional[Story] = None) -> dict:
    """Suggest a bug-reasoning class for a bug (§7.4, FR-21).

    Returns a dict with the suggested reasoning class, confidence, and explanation.
    Tries LLM first, falls back to keyword analysis.
    """
    llm_result = _llm_suggest_reasoning_class(bug, story)
    if llm_result:
        return llm_result
    return _keyword_suggest_reasoning_class(bug)


def _llm_suggest_reasoning_class(bug: Bug, story: Optional[Story] = None) -> Optional[dict]:
    """Use LLM to suggest reasoning class."""
    try:
        from openai import OpenAI

        if not settings.LLM_API_KEY and settings.LLM_API_BASE_URL == "http://localhost:11434/v1":
            client = OpenAI(
                base_url=settings.LLM_API_BASE_URL,
                api_key="not-needed",
                timeout=settings.LLM_TIMEOUT,
            )
        elif settings.LLM_API_KEY:
            client = OpenAI(
                base_url=settings.LLM_API_BASE_URL,
                api_key=settings.LLM_API_KEY,
                timeout=settings.LLM_TIMEOUT,
            )
        else:
            return None
    except Exception:
        return None

    classes = ", ".join(c.value for c in BugReasoningClass)
    story_context = ""
    if story:
        story_context = (
            f"\nRelated Story: {story.title}\n"
            f"Acceptance Criteria: {story.acceptance_criteria or 'Not specified'}\n"
        )

    prompt = f"""Classify this bug into one reasoning class.

Bug: {bug.summary}
Description: {bug.description or 'N/A'}
Severity: {bug.severity.value}
{story_context}

Classes: {classes}
- silly_miss: easily avoidable oversight, typo, careless slip
- critical_miss: serious defect in core logic, security, or data handling
- info_not_in_story: story didn't contain needed information
- missing_unit_test: developer shipped without unit coverage for this path
- wrong_test_cases: BA/tester test cases were wrong or missed the scenario

Respond in this exact format:
REASONING_CLASS: [one class]
CONFIDENCE: [0.0 to 1.0]
EXPLANATION: [1 sentence]"""

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You classify software bugs by their reasoning class. Be precise."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=150,
        )
        text = response.choices[0].message.content
        return _parse_reasoning_class_response(text)
    except Exception as e:
        logger.warning(f"LLM reasoning class suggestion failed: {e}")
        return None


def _parse_reasoning_class_response(text: str) -> Optional[dict]:
    """Parse LLM reasoning class response."""
    try:
        parsed = {}
        for line in text.strip().split("\n"):
            line = line.strip()
            if line.startswith("REASONING_CLASS:"):
                parsed["class"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("CONFIDENCE:"):
                try:
                    parsed["confidence"] = float(line.split(":", 1)[1].strip())
                except ValueError:
                    parsed["confidence"] = 0.5
            elif line.startswith("EXPLANATION:"):
                parsed["explanation"] = line.split(":", 1)[1].strip()

        class_map = {c.value: c for c in BugReasoningClass}
        reasoning_class = class_map.get(parsed.get("class", ""))
        if not reasoning_class:
            return None

        return {
            "reasoning_class": reasoning_class.value,
            "confidence": min(max(parsed.get("confidence", 0.5), 0.0), 1.0),
            "explanation": parsed.get("explanation", "LLM-based classification"),
            "method": "llm",
        }
    except Exception:
        return None


def _keyword_suggest_reasoning_class(bug: Bug) -> dict:
    """Keyword-based reasoning class suggestion (fallback)."""
    text = f"{bug.summary} {bug.description or ''}".lower()

    best_class = BugReasoningClass.SILLY_MISS
    best_score = 0.0

    for reasoning_class, keywords in REASONING_CLASS_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text)
        score = matches / len(keywords) if keywords else 0
        if score > best_score:
            best_score = score
            best_class = reasoning_class

    confidence = min(best_score * 2.5, 0.9) if best_score > 0 else 0.15

    return {
        "reasoning_class": best_class.value,
        "confidence": round(confidence, 2),
        "explanation": f"Keyword analysis matched '{best_class.value}' pattern "
                       f"with {round(confidence * 100)}% confidence.",
        "method": "keyword_rules",
    }
