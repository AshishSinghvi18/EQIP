"""Forecast service - Release risk prediction and quality forecasting (Phase 4).

Design principles (from EQIP Design Spec §16):
- Release-risk prediction based on historical quality patterns
- Quality forecast using trend analysis
- Engineering-health index
- Org benchmarking across projects
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    Bug,
    BugSeverity,
    BugStatus,
    Project,
    QualityEvent,
    QualityForecast,
    Sprint,
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


def get_quality_trend(
    db: Session, project_id: int, periods: int = 6
) -> dict:
    """Compute quality trend over recent sprints/time periods (Phase 4).

    Returns a time-series of quality metrics for trend visualization and forecasting.
    """
    sprints = (
        db.query(Sprint)
        .filter(Sprint.project_id == project_id)
        .order_by(Sprint.created_at.desc())
        .limit(periods)
        .all()
    )
    sprints.reverse()  # chronological order

    if not sprints:
        # Fall back to time-based periods (last N months)
        return _time_based_trend(db, project_id, periods)

    trend_data = []
    for sprint in sprints:
        stories = db.query(Story).filter(
            Story.project_id == project_id,
            Story.sprint_id == sprint.id,
        ).all()
        story_ids = [s.id for s in stories]

        total_bugs = (
            db.query(Bug).filter(Bug.story_id.in_(story_ids)).count()
            if story_ids else 0
        )
        done_stories = sum(
            1 for s in stories
            if s.status in [StoryStatus.DONE, StoryStatus.RELEASED]
        )

        positive_events = (
            db.query(func.count(QualityEvent.id))
            .filter(QualityEvent.story_id.in_(story_ids), QualityEvent.delta > 0)
            .scalar()
            if story_ids else 0
        ) or 0
        total_events = (
            db.query(func.count(QualityEvent.id))
            .filter(QualityEvent.story_id.in_(story_ids))
            .scalar()
            if story_ids else 0
        ) or 0

        bug_density = total_bugs / len(stories) if stories else 0
        completion_rate = done_stories / len(stories) if stories else 0
        positive_ratio = positive_events / total_events if total_events > 0 else 0.5

        trend_data.append({
            "period": sprint.name,
            "sprint_id": sprint.id,
            "stories": len(stories),
            "bugs": total_bugs,
            "bug_density": round(bug_density, 2),
            "completion_rate": round(completion_rate * 100, 1),
            "positive_event_ratio": round(positive_ratio * 100, 1),
        })

    # Compute trend direction
    forecast_direction = _compute_trend_direction(trend_data)

    return {
        "project_id": project_id,
        "periods": trend_data,
        "forecast": forecast_direction,
    }


def _time_based_trend(db: Session, project_id: int, periods: int) -> dict:
    """Fallback: compute trend using monthly time windows."""
    trend_data = []
    now = datetime.utcnow()

    for i in range(periods - 1, -1, -1):
        period_start = now - timedelta(days=30 * (i + 1))
        period_end = now - timedelta(days=30 * i)
        period_label = period_start.strftime("%Y-%m")

        stories = (
            db.query(Story)
            .filter(
                Story.project_id == project_id,
                Story.created_at >= period_start,
                Story.created_at < period_end,
            )
            .all()
        )
        story_ids = [s.id for s in stories]

        total_bugs = (
            db.query(Bug).filter(Bug.story_id.in_(story_ids)).count()
            if story_ids else 0
        )

        bug_density = total_bugs / len(stories) if stories else 0
        done_stories = sum(
            1 for s in stories
            if s.status in [StoryStatus.DONE, StoryStatus.RELEASED]
        )
        completion_rate = done_stories / len(stories) if stories else 0

        trend_data.append({
            "period": period_label,
            "sprint_id": None,
            "stories": len(stories),
            "bugs": total_bugs,
            "bug_density": round(bug_density, 2),
            "completion_rate": round(completion_rate * 100, 1),
            "positive_event_ratio": 50.0,  # default when no sprint data
        })

    forecast_direction = _compute_trend_direction(trend_data)

    return {
        "project_id": project_id,
        "periods": trend_data,
        "forecast": forecast_direction,
    }


def _compute_trend_direction(trend_data: list[dict]) -> dict:
    """Compute trend direction and predicted next-period values."""
    if len(trend_data) < 2:
        return {
            "direction": "stable",
            "bug_density_trend": "stable",
            "completion_trend": "stable",
            "predicted_bug_density": trend_data[0]["bug_density"] if trend_data else 0,
            "predicted_completion_rate": trend_data[0]["completion_rate"] if trend_data else 0,
            "confidence": 0.2,
        }

    # Simple linear trend on bug density
    densities = [p["bug_density"] for p in trend_data]
    completions = [p["completion_rate"] for p in trend_data]

    density_slope = _linear_slope(densities)
    completion_slope = _linear_slope(completions)

    # Predict next period
    predicted_density = max(0, densities[-1] + density_slope)
    predicted_completion = min(100, max(0, completions[-1] + completion_slope))

    # Determine overall direction
    if density_slope < -0.1 and completion_slope > 0.5:
        direction = "improving"
    elif density_slope > 0.1 and completion_slope < -0.5:
        direction = "declining"
    else:
        direction = "stable"

    # Confidence based on data points and consistency
    confidence = min(0.3 + len(trend_data) * 0.1, 0.85)

    return {
        "direction": direction,
        "bug_density_trend": "improving" if density_slope < -0.05 else ("declining" if density_slope > 0.05 else "stable"),
        "completion_trend": "improving" if completion_slope > 0.5 else ("declining" if completion_slope < -0.5 else "stable"),
        "predicted_bug_density": round(predicted_density, 2),
        "predicted_completion_rate": round(predicted_completion, 1),
        "confidence": round(confidence, 2),
    }


def _linear_slope(values: list[float]) -> float:
    """Compute simple linear regression slope for a list of values."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def get_org_benchmarking(db: Session) -> dict:
    """Org-level benchmarking: compare quality across all projects (Phase 4).

    Returns per-project health scores for cross-project comparison.
    """
    projects = db.query(Project).all()
    benchmarks = []

    for project in projects:
        health = get_engineering_health_index(db, project.id)
        total_stories = health["totals"]["stories"]
        total_bugs = health["totals"]["bugs"]
        bug_density = total_bugs / total_stories if total_stories > 0 else 0

        benchmarks.append({
            "project_id": project.id,
            "project_name": project.name,
            "health_index": health["health_index"],
            "zero_bug_rate": health["components"]["zero_bug_rate"],
            "production_stability": health["components"]["production_stability"],
            "bug_density": round(bug_density, 2),
            "total_stories": total_stories,
            "total_bugs": total_bugs,
        })

    # Compute org-wide averages
    if benchmarks:
        avg_health = round(sum(b["health_index"] for b in benchmarks) / len(benchmarks), 1)
        avg_bug_density = round(sum(b["bug_density"] for b in benchmarks) / len(benchmarks), 2)
    else:
        avg_health = 0
        avg_bug_density = 0

    # Sort by health index descending
    benchmarks.sort(key=lambda b: b["health_index"], reverse=True)

    return {
        "org_health_index": avg_health,
        "org_bug_density": avg_bug_density,
        "project_count": len(benchmarks),
        "projects": benchmarks,
    }
