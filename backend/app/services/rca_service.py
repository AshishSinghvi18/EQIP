"""Full-Chain Root Cause Analysis service (Phase 2, FR-6).

Design principles (from EQIP Design Spec §5):
- Traces a defect through the full delivery chain:
  Requirement → Development → Code Review → Testing → Automation → UAT → Release → Production
- Determines the TRUE origin stage (where the problem started)
- Supports shared/multi-cause ownership (percentage split)
- Uses LLM reasoning when available, with rule-based fallback

The chain matters because the same symptom can have different origins:
- If requirement never stated the rule → origin = BA/requirement
- If requirement stated it but code skipped it → origin = Developer
- If both had it but it reached production untested → origin = Testing
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import (
    Bug,
    OriginStage,
    RCAChainAnalysis,
    RootCauseCategory,
    Story,
)

logger = logging.getLogger(__name__)

# The full delivery chain (ordered)
DELIVERY_CHAIN = [
    OriginStage.REQUIREMENT,
    OriginStage.DEVELOPMENT,
    OriginStage.CODE_REVIEW,
    OriginStage.TESTING,
    OriginStage.AUTOMATION,
    OriginStage.UAT,
    OriginStage.RELEASE,
    OriginStage.PRODUCTION,
]

# Chain stage descriptions for analysis
CHAIN_STAGE_DESCRIPTIONS = {
    OriginStage.REQUIREMENT: "Requirements & acceptance criteria definition (BA)",
    OriginStage.DEVELOPMENT: "Code implementation (Developer)",
    OriginStage.CODE_REVIEW: "Peer code review",
    OriginStage.TESTING: "QA/manual testing",
    OriginStage.AUTOMATION: "Automated test coverage",
    OriginStage.UAT: "User acceptance testing",
    OriginStage.RELEASE: "Deployment & release process",
    OriginStage.PRODUCTION: "Production monitoring",
}

# Role responsible at each chain stage
CHAIN_STAGE_ROLES = {
    OriginStage.REQUIREMENT: "business_analyst",
    OriginStage.DEVELOPMENT: "developer",
    OriginStage.CODE_REVIEW: "developer",
    OriginStage.TESTING: "tester",
    OriginStage.AUTOMATION: "automation_engineer",
    OriginStage.UAT: "tester",
    OriginStage.RELEASE: "developer",
    OriginStage.PRODUCTION: "developer",
}


def _get_llm_client():
    """Get OpenAI client for LLM reasoning."""
    try:
        from openai import OpenAI

        if not settings.LLM_API_KEY and settings.LLM_API_BASE_URL == "http://localhost:11434/v1":
            return OpenAI(
                base_url=settings.LLM_API_BASE_URL,
                api_key="not-needed",
                timeout=settings.LLM_TIMEOUT,
            )
        elif settings.LLM_API_KEY:
            return OpenAI(
                base_url=settings.LLM_API_BASE_URL,
                api_key=settings.LLM_API_KEY,
                timeout=settings.LLM_TIMEOUT,
            )
        return None
    except Exception as e:
        logger.warning(f"Failed to create LLM client: {e}")
        return None


def analyze_full_chain(db: Session, bug_id: int) -> Optional[RCAChainAnalysis]:
    """Perform full-chain root cause analysis for a bug (FR-6).

    Traces the defect through the entire delivery chain to find:
    1. Where in the chain the problem ORIGINATED
    2. Which stages SHOULD have caught it but didn't
    3. How ownership should be split across roles

    Uses LLM analysis when available, falls back to rule-based analysis.
    """
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        return None

    # Get the story context if available
    story = None
    if bug.story_id:
        story = db.query(Story).filter(Story.id == bug.story_id).first()

    # Try LLM-based analysis first
    llm_result = _llm_chain_analysis(bug, story)

    if llm_result:
        chain_analysis = llm_result
    else:
        # Fall back to rule-based analysis
        chain_analysis = _rule_based_chain_analysis(bug, story)

    # Store the analysis
    rca = RCAChainAnalysis(
        bug_id=bug_id,
        chain_stages=chain_analysis["chain_stages"],
        root_origin_stage=chain_analysis["root_origin_stage"],
        contributing_factors=chain_analysis["contributing_factors"],
        ownership_split=chain_analysis["ownership_split"],
        ai_confidence=chain_analysis["confidence"],
        reasoning=chain_analysis["reasoning"],
        analyzed_by="ai" if llm_result else "rule_engine",
    )
    db.add(rca)
    db.commit()
    db.refresh(rca)
    return rca


def _llm_chain_analysis(bug: Bug, story: Optional[Story]) -> Optional[dict]:
    """Use LLM to perform full-chain RCA analysis."""
    client = _get_llm_client()
    if not client:
        return None

    # Build context for the LLM
    story_context = ""
    if story:
        story_context = (
            f"\nStory: {story.title}\n"
            f"Acceptance Criteria: {story.acceptance_criteria or 'Not specified'}\n"
            f"Module: {story.module or 'Unknown'}\n"
        )

    prompt = f"""Analyze this software defect and trace it through the delivery chain to find its TRUE root cause origin.

Bug Summary: {bug.summary}
Bug Description: {bug.description or 'No description'}
Severity: {bug.severity.value}
Detected Stage: {bug.detected_stage.value if bug.detected_stage else 'Unknown'}
Root Cause Notes: {bug.root_cause or 'None provided'}
{story_context}

The delivery chain stages are:
1. Requirement (BA defines requirements/acceptance criteria)
2. Development (Developer implements the code)
3. Code Review (Peer review catches issues)
4. Testing (QA testing)
5. Automation (Automated test coverage)
6. UAT (User acceptance testing)
7. Release (Deployment process)
8. Production (Monitoring)

For this defect, determine:
1. Which stage is the TRUE origin (where did the problem START)?
2. Which stages should have caught it but failed to?
3. What percentage of ownership should each contributing role have?

Respond in this exact format:
ORIGIN: [stage name - one of: requirement, development, code_review, testing, automation, uat, release, production]
REASONING: [1-2 sentence explanation of why this is the origin]
OWNERSHIP: [role:percentage pairs, must sum to 100, e.g. developer:60,tester:30,business_analyst:10]
MISSED_BY: [comma-separated stages that should have caught it]
CONFIDENCE: [0.0 to 1.0]"""

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a software quality analyst specializing in root cause analysis. "
                        "You trace defects to their true origin in the delivery chain. "
                        "Be precise and evidence-based."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )

        result_text = response.choices[0].message.content
        return _parse_llm_rca_response(result_text, bug)
    except Exception as e:
        logger.warning(f"LLM chain analysis failed: {e}")
        return None


def _parse_llm_rca_response(text: str, bug: Bug) -> Optional[dict]:
    """Parse the LLM's structured response into a chain analysis dict."""
    try:
        lines = text.strip().split("\n")
        result = {}
        for line in lines:
            line = line.strip()
            if line.startswith("ORIGIN:"):
                result["origin"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.split(":", 1)[1].strip()
            elif line.startswith("OWNERSHIP:"):
                ownership_str = line.split(":", 1)[1].strip()
                result["ownership"] = _parse_ownership(ownership_str)
            elif line.startswith("MISSED_BY:"):
                missed_str = line.split(":", 1)[1].strip()
                result["missed_by"] = [s.strip() for s in missed_str.split(",")]
            elif line.startswith("CONFIDENCE:"):
                try:
                    result["confidence"] = float(line.split(":", 1)[1].strip())
                except ValueError:
                    result["confidence"] = 0.5

        if "origin" not in result:
            return None

        # Map origin string to enum
        origin_map = {s.value: s for s in OriginStage}
        root_origin = origin_map.get(result["origin"], OriginStage.DEVELOPMENT)

        # Build chain stages analysis
        chain_stages = _build_chain_stages(root_origin, result.get("missed_by", []))

        return {
            "chain_stages": chain_stages,
            "root_origin_stage": root_origin,
            "contributing_factors": result.get("missed_by", []),
            "ownership_split": result.get("ownership", {"developer": 50, "tester": 30, "business_analyst": 20}),
            "confidence": result.get("confidence", 0.5),
            "reasoning": result.get("reasoning", "LLM analysis"),
        }
    except Exception as e:
        logger.warning(f"Failed to parse LLM RCA response: {e}")
        return None


def _parse_ownership(ownership_str: str) -> dict:
    """Parse ownership string like 'developer:60,tester:30,business_analyst:10'."""
    ownership = {}
    pairs = ownership_str.split(",")
    for pair in pairs:
        parts = pair.strip().split(":")
        if len(parts) == 2:
            role = parts[0].strip()
            try:
                pct = int(parts[1].strip())
                ownership[role] = pct
            except ValueError:
                pass
    return ownership if ownership else {"developer": 50, "tester": 30, "business_analyst": 20}


def _build_chain_stages(
    root_origin: OriginStage, missed_by: list[str]
) -> list[dict]:
    """Build the chain stages analysis showing what happened at each stage."""
    stages = []
    origin_idx = DELIVERY_CHAIN.index(root_origin) if root_origin in DELIVERY_CHAIN else 1

    for i, stage in enumerate(DELIVERY_CHAIN):
        stage_info = {
            "stage": stage.value,
            "description": CHAIN_STAGE_DESCRIPTIONS[stage],
            "responsible_role": CHAIN_STAGE_ROLES[stage],
            "status": "not_applicable",
        }

        if i == origin_idx:
            stage_info["status"] = "origin"
            stage_info["note"] = "Defect originated at this stage"
        elif i > origin_idx and stage.value in missed_by:
            stage_info["status"] = "missed"
            stage_info["note"] = "Should have caught the defect but did not"
        elif i > origin_idx:
            stage_info["status"] = "passed_through"

        stages.append(stage_info)

    return stages


def _rule_based_chain_analysis(bug: Bug, story: Optional[Story]) -> dict:
    """Rule-based full-chain RCA when LLM is unavailable.

    Uses keyword analysis and detected stage to determine origin.
    """
    text = f"{bug.summary} {bug.description or ''}".lower()

    # Determine root origin based on keywords and category
    root_origin = OriginStage.DEVELOPMENT  # default
    confidence = 0.4

    # Requirement-origin indicators
    req_keywords = [
        "requirement", "spec", "not specified", "missing criteria",
        "ambiguous", "unclear", "acceptance criteria",
    ]
    dev_keywords = [
        "logic", "code", "implementation", "null pointer", "exception",
        "validation", "missing check", "off-by-one",
    ]
    test_keywords = [
        "not tested", "missed test", "regression", "edge case not covered",
        "no automation", "test gap",
    ]

    req_score = sum(1 for kw in req_keywords if kw in text)
    dev_score = sum(1 for kw in dev_keywords if kw in text)
    test_score = sum(1 for kw in test_keywords if kw in text)

    # Use existing root_cause_category if set
    if bug.root_cause_category:
        from app.services.ai_service import ORIGIN_STAGE_MAP
        if bug.root_cause_category in ORIGIN_STAGE_MAP:
            root_origin = ORIGIN_STAGE_MAP[bug.root_cause_category]
            confidence = 0.6
    elif req_score > dev_score and req_score > test_score:
        root_origin = OriginStage.REQUIREMENT
        confidence = min(req_score * 0.15 + 0.3, 0.7)
    elif test_score > dev_score:
        root_origin = OriginStage.TESTING
        confidence = min(test_score * 0.15 + 0.3, 0.7)
    else:
        root_origin = OriginStage.DEVELOPMENT
        confidence = min(dev_score * 0.15 + 0.3, 0.7) if dev_score > 0 else 0.3

    # Determine which stages missed it based on detected_stage
    missed_by = []
    if bug.detected_stage:
        origin_idx = DELIVERY_CHAIN.index(root_origin) if root_origin in DELIVERY_CHAIN else 1
        # Stages between origin and detection that should have caught it
        detection_stage_map = {
            "code_review": OriginStage.CODE_REVIEW,
            "unit_testing": OriginStage.TESTING,
            "integration_testing": OriginStage.TESTING,
            "qa_testing": OriginStage.TESTING,
            "uat": OriginStage.UAT,
            "staging": OriginStage.RELEASE,
            "production": OriginStage.PRODUCTION,
        }
        detected_chain_stage = detection_stage_map.get(
            bug.detected_stage.value, OriginStage.PRODUCTION
        )
        detected_idx = (
            DELIVERY_CHAIN.index(detected_chain_stage)
            if detected_chain_stage in DELIVERY_CHAIN
            else len(DELIVERY_CHAIN) - 1
        )

        for i in range(origin_idx + 1, detected_idx):
            missed_by.append(DELIVERY_CHAIN[i].value)

    # Build ownership split
    ownership_split = _determine_ownership(root_origin, missed_by)

    # Build chain stages
    chain_stages = _build_chain_stages(root_origin, missed_by)

    reasoning = (
        f"Rule-based analysis: Root cause traced to '{root_origin.value}' stage. "
        f"{'Stages that missed it: ' + ', '.join(missed_by) + '.' if missed_by else 'No intermediate stages missed.'}"
    )

    return {
        "chain_stages": chain_stages,
        "root_origin_stage": root_origin,
        "contributing_factors": missed_by,
        "ownership_split": ownership_split,
        "confidence": confidence,
        "reasoning": reasoning,
    }


def _determine_ownership(root_origin: OriginStage, missed_by: list[str]) -> dict:
    """Determine ownership split based on origin and stages that missed the defect.

    The origin stage gets the majority, but stages that should have caught it
    share some responsibility (Design Spec §5.3).
    """
    ownership = {}
    primary_role = CHAIN_STAGE_ROLES.get(root_origin, "developer")

    if not missed_by:
        # Single owner
        ownership[primary_role] = 100
    else:
        # Split ownership: primary gets 50-70%, missed stages share the rest
        primary_pct = 60
        remaining = 100 - primary_pct
        per_missed = remaining // len(missed_by) if missed_by else 0

        ownership[primary_role] = primary_pct
        for stage_value in missed_by:
            try:
                stage = OriginStage(stage_value)
                role = CHAIN_STAGE_ROLES.get(stage, "developer")
                ownership[role] = ownership.get(role, 0) + per_missed
            except ValueError:
                pass

        # Ensure percentages sum to 100
        total = sum(ownership.values())
        if total < 100:
            ownership[primary_role] += 100 - total

    return ownership


def get_chain_analysis(db: Session, bug_id: int) -> Optional[RCAChainAnalysis]:
    """Get existing chain analysis for a bug."""
    return (
        db.query(RCAChainAnalysis)
        .filter(RCAChainAnalysis.bug_id == bug_id)
        .order_by(RCAChainAnalysis.created_at.desc())
        .first()
    )


def get_chain_summary(db: Session, project_id: Optional[int] = None) -> dict:
    """Get aggregated chain analysis summary showing where defects originate.

    Returns a breakdown of origin stages and their frequency,
    useful for the chain view dashboard (Design Spec §10.3).
    """
    query = db.query(RCAChainAnalysis)
    analyses = query.all()

    if not analyses:
        return {"total_analyzed": 0, "origin_distribution": {}, "common_missed_stages": {}}

    origin_counts = {}
    missed_counts = {}

    for analysis in analyses:
        # Count origins
        origin = analysis.root_origin_stage.value
        origin_counts[origin] = origin_counts.get(origin, 0) + 1

        # Count missed stages
        if analysis.contributing_factors:
            for stage in analysis.contributing_factors:
                missed_counts[stage] = missed_counts.get(stage, 0) + 1

    total = len(analyses)
    origin_distribution = {k: round(v / total * 100, 1) for k, v in origin_counts.items()}
    missed_distribution = {k: round(v / total * 100, 1) for k, v in missed_counts.items()}

    return {
        "total_analyzed": total,
        "origin_distribution": origin_distribution,
        "common_missed_stages": missed_distribution,
    }
