from __future__ import annotations

from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.pydantic_schemas import (
    BreakdownItem,
    BugBreakdownResponse,
    ChainViewItem,
    ChainViewResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    ModuleHeatmapItem,
    ModuleHeatmapResponse,
    OverviewCard,
    OverviewResponse,
    RootCauseBreakdownResponse,
    StoryDrilldown,
    TrendPoint,
    TrendResponse,
)
from app.models.schemas import Bug, DetectionStage, Story, UserRole
from app.services.scoring_engine import SEVERITY_WEIGHTS, fetch_leaderboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _load_scope(db: Session) -> tuple[list[Story], list[Bug]]:
    stories = list(db.scalars(select(Story).options(selectinload(Story.sprint), selectinload(Story.project))).all())
    bugs = list(db.scalars(select(Bug).options(selectinload(Bug.story), selectinload(Bug.detected_by))).all())
    return stories, bugs


def _quality_index(stories: list[Story], bugs: list[Bug]) -> float:
    story_count = max(len(stories), 1)
    weighted_defects = sum(SEVERITY_WEIGHTS[bug.severity.value] for bug in bugs)
    escaped = sum(1 for bug in bugs if bug.detected_stage == DetectionStage.PRODUCTION)
    early = sum(1 for bug in bugs if bug.detected_stage in {DetectionStage.CODE_REVIEW, DetectionStage.TESTING, DetectionStage.AUTOMATION})
    base = 100 - (weighted_defects / story_count) * 3.1 - escaped * 1.8 + (early / max(len(bugs), 1)) * 18
    return round(max(0.0, min(100.0, base)), 2)


@router.get("/overview", response_model=OverviewResponse)
def dashboard_overview(db: Session = Depends(get_db)) -> OverviewResponse:
    stories, bugs = _load_scope(db)
    latest_sprint = max((story.sprint for story in stories if story.sprint), key=lambda sprint: sprint.end_date)
    latest_stories = [story for story in stories if story.sprint_id == latest_sprint.id]
    latest_bugs = [bug for bug in bugs if bug.sprint_id == latest_sprint.id]
    production_defects = sum(1 for bug in bugs if bug.detected_stage == DetectionStage.PRODUCTION)
    escaped_pct = round((production_defects / max(len(bugs), 1)) * 100, 2)
    zero_bug_stories = sum(1 for story in stories if not story.bugs)
    automation_coverage = round((sum(1 for story in stories if story.automation_id is not None) / max(len(stories), 1)) * 100, 2)
    early_detection_rate = round((sum(1 for bug in bugs if bug.detected_stage in {DetectionStage.CODE_REVIEW, DetectionStage.TESTING, DetectionStage.AUTOMATION}) / max(len(bugs), 1)) * 100, 2)
    cards = [
        OverviewCard(label="quality_index", value=_quality_index(stories, bugs), unit="score", context="All active data"),
        OverviewCard(label="sprint_quality", value=_quality_index(latest_stories, latest_bugs), unit="score", context=latest_sprint.name),
        OverviewCard(label="production_defects", value=production_defects, unit="bugs"),
        OverviewCard(label="escaped_defect_rate", value=escaped_pct, unit="%"),
        OverviewCard(label="early_detection_rate", value=early_detection_rate, unit="%"),
        OverviewCard(label="automation_coverage", value=automation_coverage, unit="%"),
        OverviewCard(label="zero_bug_stories", value=zero_bug_stories, unit="stories"),
    ]
    return OverviewResponse(cards=cards)


@router.get("/module-heatmap", response_model=ModuleHeatmapResponse)
def module_heatmap(db: Session = Depends(get_db)) -> ModuleHeatmapResponse:
    stories, bugs = _load_scope(db)
    story_groups = defaultdict(list)
    bug_groups = defaultdict(list)
    for story in stories:
        story_groups[story.module].append(story)
    for bug in bugs:
        bug_groups[bug.module].append(bug)
    items = []
    for module in sorted(story_groups):
        module_stories = story_groups[module]
        module_bugs = bug_groups[module]
        bug_count = len(module_bugs)
        story_count = len(module_stories)
        escaped_count = sum(1 for bug in module_bugs if bug.detected_stage == DetectionStage.PRODUCTION)
        severity_index = round(sum(SEVERITY_WEIGHTS[bug.severity.value] for bug in module_bugs) / max(bug_count, 1), 2)
        defect_density = round(bug_count / max(story_count, 1), 2)
        escaped_rate = round((escaped_count / max(bug_count, 1)) * 100, 2)
        quality_index = round(max(0.0, min(100.0, 100 - defect_density * 14 - escaped_rate * 0.22 - severity_index * 3.2)), 2)
        items.append(ModuleHeatmapItem(module=module, label=module, story_count=story_count, bug_count=bug_count, defect_density=defect_density, escaped_defect_rate=escaped_rate, severity_index=severity_index, quality_index=quality_index))
    return ModuleHeatmapResponse(items=items)


@router.get("/bug-breakdown", response_model=BugBreakdownResponse)
def bug_breakdown(module: str, db: Session = Depends(get_db)) -> BugBreakdownResponse:
    bugs = list(db.scalars(select(Bug).where(Bug.module == module).options(selectinload(Bug.story))).all())
    groups: dict[str, list[Bug]] = defaultdict(list)
    for bug in bugs:
        groups[bug.root_cause_category.value].append(bug)
    items = []
    for label, grouped_bugs in sorted(groups.items(), key=lambda item: len(item[1]), reverse=True):
        items.append(BreakdownItem(label=label, value=round(sum(SEVERITY_WEIGHTS[bug.severity.value] for bug in grouped_bugs), 2), count=len(grouped_bugs)))
    return BugBreakdownResponse(module=module, items=items)


@router.get("/root-cause-breakdown", response_model=RootCauseBreakdownResponse)
def root_cause_breakdown(module: str, category: str, db: Session = Depends(get_db)) -> RootCauseBreakdownResponse:
    bugs = list(
        db.scalars(
            select(Bug)
            .where(Bug.module == module)
            .options(selectinload(Bug.story))
        ).all()
    )
    filtered = [bug for bug in bugs if bug.root_cause_category.value == category]
    groups: dict[str, list[Bug]] = defaultdict(list)
    for bug in filtered:
        groups[bug.root_cause or bug.root_cause_category.value].append(bug)
    items = []
    for label, grouped_bugs in sorted(groups.items(), key=lambda item: len(item[1]), reverse=True):
        drilldown = [
            StoryDrilldown(
                story_id=bug.story.id,
                story_key=bug.story.story_key,
                title=bug.story.title,
                bug_key=bug.bug_key,
                summary=bug.summary,
                root_cause=bug.root_cause,
            )
            for bug in grouped_bugs
        ]
        items.append(BreakdownItem(label=label, value=round(sum(SEVERITY_WEIGHTS[bug.severity.value] for bug in grouped_bugs), 2), count=len(grouped_bugs), stories=drilldown))
    return RootCauseBreakdownResponse(module=module, category=category, items=items)


@router.get("/trend", response_model=TrendResponse)
def quality_trend(db: Session = Depends(get_db)) -> TrendResponse:
    stories, bugs = _load_scope(db)
    sprint_map = {story.sprint_id: story.sprint for story in stories if story.sprint is not None}
    points = []
    for sprint_id, sprint in sorted(sprint_map.items(), key=lambda item: item[1].start_date):
        sprint_stories = [story for story in stories if story.sprint_id == sprint_id]
        sprint_bugs = [bug for bug in bugs if bug.sprint_id == sprint_id]
        production_defects = sum(1 for bug in sprint_bugs if bug.detected_stage == DetectionStage.PRODUCTION)
        points.append(
            TrendPoint(
                label=sprint.name,
                value=_quality_index(sprint_stories, sprint_bugs),
                escaped_defect_rate=round((production_defects / max(len(sprint_bugs), 1)) * 100, 2),
                production_defects=production_defects,
                story_count=len(sprint_stories),
                bug_count=len(sprint_bugs),
            )
        )
    return TrendResponse(items=points)


@router.get("/leaderboard", response_model=LeaderboardResponse)
def dashboard_leaderboard(
    role: UserRole | None = None,
    limit: int = Query(default=8, ge=1, le=25),
    db: Session = Depends(get_db),
) -> LeaderboardResponse:
    scores = fetch_leaderboard(db, role=role, limit=limit)
    items = [
        LeaderboardEntry(
            user_id=score.actor_id,
            name=score.actor.full_name,
            role=score.role,
            score=score.computed_value,
            facts=[f"{entry['label']} {entry['value']}" for entry in score.breakdown.get("top_event_types", [])[:3]],
        )
        for score in scores
    ]
    return LeaderboardResponse(items=items)


@router.get("/chain-view", response_model=ChainViewResponse)
def chain_view(
    module: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
) -> ChainViewResponse:
    bugs = list(db.scalars(select(Bug)).all())
    if module is not None:
        bugs = [bug for bug in bugs if bug.module == module]
    if category is not None:
        bugs = [bug for bug in bugs if bug.root_cause_category.value == category]
    bucket: Counter[tuple[DetectionStage, DetectionStage]] = Counter()
    impact: defaultdict[tuple[DetectionStage, DetectionStage], float] = defaultdict(float)
    for bug in bugs:
        key = (bug.origin_stage, bug.detected_stage)
        bucket[key] += 1
        impact[key] += SEVERITY_WEIGHTS[bug.severity.value]
    items = [
        ChainViewItem(origin_stage=origin, detected_stage=detected, count=count, weighted_impact=round(impact[(origin, detected)], 2))
        for (origin, detected), count in sorted(bucket.items(), key=lambda item: impact[item[0]], reverse=True)
    ]
    return ChainViewResponse(items=items)
