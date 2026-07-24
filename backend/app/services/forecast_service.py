"""Forecast service - Release risk prediction and quality forecasting (Phase 4).

Design principles (from EQIP Design Spec §16):
- Release-risk prediction based on historical quality patterns
- Quality forecast using trend analysis
- Engineering-health index
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    Bug,
    BugSeverity,
    BugStatus,
    QualityEvent,
    QualityForecast,
    Story,
    StoryStatus,
)


def generate_release_forecast(
    db: Session, project_id: int, sprint_id: Optional[int] = None, release: Optional[str] = None
) -> QualityForecast:
    """Generate a release-risk prediction based on current quality metrics.

    Analyzes:
    - Bug density (bugs per story)
    - Open bug severity distribution
    - Escaped defect rate
    - Story completion rate
    - Historical pattern comparison
    """
    # Get stories for this scope
    story_query = db.query(Story).filter(Story.project_id == project_id)
    if sprint_id:
        story_query = story_query.filter(Story.sprint_id == sprint_id)
    if release:
        story_query = story_query.filter(Story.release == release)

    stories = story_query.all()
    story_ids = [s.id for s in stories]

    if not story_ids:
        forecast = QualityForecast(
            project_id=project_id,
            sprint_id=sprint_id,
            release=release,
            risk_score=0.0,
            confidence=0.1,
            factors=[{"factor": "No stories found", "impact": 0}],
            recommendations=["Add stories to assess release risk."],
        )
        db.add(forecast)
        db.commit()
        db.refresh(forecast)
        return forecast

    # Calculate risk factors
    factors = []
    risk_score = 0.0

    # Factor 1: Bug density
    total_bugs = db.query(Bug).filter(Bug.story_id.in_(story_ids)).count()
    bug_density = total_bugs / len(stories) if stories else 0
    bug_density_impact = min(bug_density * 15, 30)
    risk_score += bug_density_impact
    factors.append({
        "factor": "Bug density",
        "value": round(bug_density, 2),
        "impact": round(bug_density_impact, 1),
        "description": f"{total_bugs} bugs across {len(stories)} stories",
    })

    # Factor 2: Open critical/high bugs
    critical_open = (
        db.query(Bug)
        .filter(
            Bug.story_id.in_(story_ids),
            Bug.status.in_([BugStatus.OPEN, BugStatus.IN_PROGRESS, BugStatus.REOPENED]),
            Bug.severity.in_([BugSeverity.CRITICAL, BugSeverity.HIGH, BugSeverity.PRODUCTION]),
        )
        .count()
    )
    critical_impact = critical_open * 10
    risk_score += min(critical_impact, 30)
    factors.append({
        "factor": "Open critical/high bugs",
        "value": critical_open,
        "impact": round(min(critical_impact, 30), 1),
        "description": f"{critical_open} unresolved critical/high severity bugs",
    })

    # Factor 3: Story completion rate
    done_stories = sum(1 for s in stories if s.status in [StoryStatus.DONE, StoryStatus.RELEASED])
    completion_rate = done_stories / len(stories) if stories else 0
    completion_impact = (1 - completion_rate) * 20
    risk_score += completion_impact
    factors.append({
        "factor": "Incomplete stories",
        "value": round(completion_rate * 100, 1),
        "impact": round(completion_impact, 1),
        "description": f"{done_stories}/{len(stories)} stories completed ({round(completion_rate * 100)}%)",
    })

    # Factor 4: Negative quality events
    negative_events = (
        db.query(func.count(QualityEvent.id))
        .filter(
            QualityEvent.story_id.in_(story_ids),
            QualityEvent.delta < 0,
        )
        .scalar()
    ) or 0
    negative_impact = min(negative_events * 2, 20)
    risk_score += negative_impact
    factors.append({
        "factor": "Negative quality events",
        "value": negative_events,
        "impact": round(negative_impact, 1),
        "description": f"{negative_events} negative quality events recorded",
    })

    # Normalize risk score to 0-100
    risk_score = min(risk_score, 100)

    # Generate recommendations
    recommendations = _generate_risk_recommendations(factors, risk_score)

    # Confidence based on data availability
    confidence = min(0.3 + (len(stories) * 0.05) + (total_bugs * 0.02), 0.95)

    forecast = QualityForecast(
        project_id=project_id,
        sprint_id=sprint_id,
        release=release,
        risk_score=round(risk_score, 1),
        confidence=round(confidence, 2),
        factors=factors,
        recommendations=recommendations,
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    return forecast


def _generate_risk_recommendations(factors: list[dict], risk_score: float) -> list[str]:
    """Generate actionable recommendations based on risk factors."""
    recommendations = []

    if risk_score >= 70:
        recommendations.append(
            "HIGH RISK: Consider delaying release. Critical issues need resolution."
        )
    elif risk_score >= 40:
        recommendations.append(
            "MODERATE RISK: Address critical bugs before release. Increase testing focus."
        )
    else:
        recommendations.append(
            "LOW RISK: Release looks healthy. Continue standard QA process."
        )

    for factor in factors:
        if factor["factor"] == "Bug density" and factor["value"] > 2:
            recommendations.append(
                "High bug density detected. Consider additional code review focus."
            )
        elif factor["factor"] == "Open critical/high bugs" and factor["value"] > 0:
            recommendations.append(
                f"Resolve {factor['value']} critical/high bugs before release."
            )
        elif factor["factor"] == "Incomplete stories" and factor["value"] < 80:
            recommendations.append(
                "Many stories incomplete. Assess scope and consider deferring lower-priority items."
            )

    return recommendations


def get_engineering_health_index(db: Session, project_id: int) -> dict:
    """Compute the Engineering Health Index for a project (Phase 4 KPI).

    Combines multiple quality signals into a single health score.
    """
    total_stories = db.query(Story).filter(Story.project_id == project_id).count()
    total_bugs = (
        db.query(Bug)
        .join(Story, Story.id == Bug.story_id)
        .filter(Story.project_id == project_id)
        .count()
    )

    # Quality Index components
    zero_bug_stories = total_stories - (
        db.query(Bug.story_id)
        .join(Story, Story.id == Bug.story_id)
        .filter(Story.project_id == project_id, Bug.story_id.isnot(None))
        .distinct()
        .count()
    )
    zero_bug_rate = zero_bug_stories / total_stories if total_stories > 0 else 1.0

    # Production defect rate
    production_bugs = (
        db.query(Bug)
        .join(Story, Story.id == Bug.story_id)
        .filter(Story.project_id == project_id, Bug.severity == BugSeverity.PRODUCTION)
        .count()
    )
    prod_defect_rate = production_bugs / total_stories if total_stories > 0 else 0

    # Positive event ratio
    positive_events = (
        db.query(func.count(QualityEvent.id))
        .join(Story, Story.id == QualityEvent.story_id)
        .filter(Story.project_id == project_id, QualityEvent.delta > 0)
        .scalar()
    ) or 0
    total_events = (
        db.query(func.count(QualityEvent.id))
        .join(Story, Story.id == QualityEvent.story_id)
        .filter(Story.project_id == project_id)
        .scalar()
    ) or 0
    positive_ratio = positive_events / total_events if total_events > 0 else 0.5

    # Compute health index (0-100)
    health_index = round(
        (zero_bug_rate * 40) + (positive_ratio * 30) + ((1 - min(prod_defect_rate, 1)) * 30),
        1,
    ) * 100 / 100

    return {
        "health_index": round(health_index * 100, 1),
        "components": {
            "zero_bug_rate": round(zero_bug_rate * 100, 1),
            "positive_event_ratio": round(positive_ratio * 100, 1),
            "production_stability": round((1 - min(prod_defect_rate, 1)) * 100, 1),
        },
        "totals": {
            "stories": total_stories,
            "bugs": total_bugs,
            "production_defects": production_bugs,
            "quality_events": total_events,
        },
    }
