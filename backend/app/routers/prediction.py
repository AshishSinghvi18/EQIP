"""Phase 4 Prediction endpoints: release-risk, quality forecast, org benchmarking, health index."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import QualityForecast
from app.schemas import (
    HealthIndexResponse,
    OrgBenchmarkResponse,
    QualityForecastResponse,
    QualityTrendResponse,
)
from app.services.forecast_service import (
    generate_release_forecast,
    get_engineering_health_index,
    get_org_benchmarking,
    get_quality_trend,
)

router = APIRouter(prefix="/prediction", tags=["prediction (Phase 4)"])


@router.post("/forecast", response_model=QualityForecastResponse)
def create_release_forecast(
    project_id: int = Query(...),
    sprint_id: int | None = Query(None),
    release: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Generate a release-risk prediction based on current quality metrics.

    Analyzes bug density, open severity distribution, escaped defect rate,
    story completion rate, and historical patterns to compute a 0-100 risk score.
    Returns risk factors with impact weights and actionable recommendations.
    """
    return generate_release_forecast(db, project_id, sprint_id, release)


@router.get("/forecast/{project_id}", response_model=list[QualityForecastResponse])
def get_forecasts(
    project_id: int,
    limit: int = Query(10),
    db: Session = Depends(get_db),
):
    """Get recent release-risk forecasts for a project."""
    return (
        db.query(QualityForecast)
        .filter(QualityForecast.project_id == project_id)
        .order_by(QualityForecast.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/trend/{project_id}", response_model=QualityTrendResponse)
def get_quality_trend_endpoint(
    project_id: int,
    periods: int = Query(6, ge=2, le=24),
    db: Session = Depends(get_db),
):
    """Get quality trend over recent sprints with forecasted direction.

    Returns time-series data of bug density, completion rate, and positive event ratio.
    Includes a linear-regression-based forecast of next-period values.
    """
    return get_quality_trend(db, project_id, periods)


@router.get("/health/{project_id}", response_model=HealthIndexResponse)
def get_health_index(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Compute the Engineering Health Index for a project (Phase 4 KPI).

    Combines: zero-bug rate (40%), positive event ratio (30%),
    production stability (30%) into a single 0-100 score.
    """
    return get_engineering_health_index(db, project_id)


@router.get("/benchmarking", response_model=OrgBenchmarkResponse)
def get_org_benchmark(db: Session = Depends(get_db)):
    """Org-level benchmarking: compare quality metrics across all projects.

    Returns per-project health scores ranked for cross-project comparison,
    plus org-wide averages.
    """
    return get_org_benchmarking(db)
