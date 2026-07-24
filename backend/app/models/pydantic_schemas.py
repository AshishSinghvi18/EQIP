from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.schemas import BugStatus, DetectionStage, RootCauseCategory, SeverityLevel, SprintStatus, StoryStatus, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    full_name: str
    email: str
    role: UserRole
    team: str | None = None
    avatar_url: str | None = None
    active: bool = True


class UserCreate(UserBase):
    pass


class UserRead(UserBase, ORMModel):
    id: int
    created_at: datetime


class ProjectBase(BaseModel):
    key: str
    name: str
    description: str | None = None
    status: str = "Active"


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase, ORMModel):
    id: int
    created_at: datetime


class SprintBase(BaseModel):
    name: str
    goal: str | None = None
    project_id: int
    start_date: date
    end_date: date
    release_name: str | None = None
    status: SprintStatus = SprintStatus.PLANNED


class SprintCreate(SprintBase):
    pass


class SprintRead(SprintBase, ORMModel):
    id: int
    created_at: datetime


class UserSummary(ORMModel):
    id: int
    full_name: str
    role: UserRole
    team: str | None = None


class ProjectSummary(ORMModel):
    id: int
    key: str
    name: str


class SprintSummary(ORMModel):
    id: int
    name: str
    status: SprintStatus
    release_name: str | None = None
    start_date: date
    end_date: date


class StoryBase(BaseModel):
    story_key: str
    title: str
    epic: str | None = None
    project_id: int
    sprint_id: int
    module: str
    priority: str | None = None
    complexity: str | None = None
    story_points: int = 3
    acceptance_criteria: str | None = None
    ba_id: int | None = None
    developer_id: int | None = None
    tester_id: int | None = None
    automation_id: int | None = None
    reviewer_id: int | None = None
    status: StoryStatus = StoryStatus.DRAFT
    estimated_date: date | None = None
    completion_date: date | None = None
    release_name: str | None = None
    environment: str | None = None
    attachments: list[Any] = Field(default_factory=list)
    documentation: str | None = None


class StoryCreate(StoryBase):
    pass


class StoryUpdate(BaseModel):
    title: str | None = None
    epic: str | None = None
    sprint_id: int | None = None
    module: str | None = None
    priority: str | None = None
    complexity: str | None = None
    story_points: int | None = None
    acceptance_criteria: str | None = None
    ba_id: int | None = None
    developer_id: int | None = None
    tester_id: int | None = None
    automation_id: int | None = None
    reviewer_id: int | None = None
    status: StoryStatus | None = None
    estimated_date: date | None = None
    completion_date: date | None = None
    release_name: str | None = None
    environment: str | None = None
    attachments: list[Any] | None = None
    documentation: str | None = None


class StoryRead(StoryBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime
    project: ProjectSummary | None = None
    sprint: SprintSummary | None = None
    ba: UserSummary | None = None
    developer: UserSummary | None = None
    tester: UserSummary | None = None
    automation_engineer: UserSummary | None = None
    reviewer: UserSummary | None = None


class StoryListResponse(BaseModel):
    items: list[StoryRead]
    total: int


class BugBase(BaseModel):
    bug_key: str
    story_id: int
    project_id: int
    sprint_id: int
    module: str
    summary: str
    description: str | None = None
    severity: SeverityLevel
    priority: str | None = None
    environment: str | None = None
    detected_by_id: int | None = None
    detected_stage: DetectionStage
    assigned_to_id: int | None = None
    root_cause: str | None = None
    root_cause_category: RootCauseCategory
    origin_stage: DetectionStage
    ownership_split: dict[str, float] = Field(default_factory=dict)
    bug_category: str | None = None
    resolution: str | None = None
    status: BugStatus = BugStatus.OPEN
    created_date: datetime | None = None
    closed_date: datetime | None = None
    ai_suggested: dict[str, Any] = Field(default_factory=dict)
    ai_confidence: float | None = None
    human_approved_by_id: int | None = None
    human_approved_at: datetime | None = None

    @field_validator("ownership_split")
    @classmethod
    def validate_ownership_split(cls, value: dict[str, float]) -> dict[str, float]:
        if not value:
            return value
        total = sum(float(part) for part in value.values())
        if total <= 0 or total > 1.05:
            raise ValueError("ownership_split must sum to a value between 0 and 1")
        return value


class BugCreate(BugBase):
    pass


class BugUpdate(BaseModel):
    sprint_id: int | None = None
    module: str | None = None
    summary: str | None = None
    description: str | None = None
    severity: SeverityLevel | None = None
    priority: str | None = None
    environment: str | None = None
    detected_by_id: int | None = None
    detected_stage: DetectionStage | None = None
    assigned_to_id: int | None = None
    root_cause: str | None = None
    root_cause_category: RootCauseCategory | None = None
    origin_stage: DetectionStage | None = None
    ownership_split: dict[str, float] | None = None
    bug_category: str | None = None
    resolution: str | None = None
    status: BugStatus | None = None
    closed_date: datetime | None = None
    ai_suggested: dict[str, Any] | None = None
    ai_confidence: float | None = None
    human_approved_by_id: int | None = None
    human_approved_at: datetime | None = None


class StoryDrilldown(ORMModel):
    story_id: int
    story_key: str
    title: str
    bug_key: str
    summary: str
    root_cause: str | None = None


class BugRead(BugBase, ORMModel):
    id: int
    story: StoryRead | None = None
    project: ProjectSummary | None = None
    sprint: SprintSummary | None = None
    detected_by: UserSummary | None = None
    assigned_to: UserSummary | None = None
    human_approved_by: UserSummary | None = None


class BugListResponse(BaseModel):
    items: list[BugRead]
    total: int


class QualityEventRead(ORMModel):
    id: int
    story_id: int | None = None
    bug_id: int | None = None
    project_id: int | None = None
    sprint_id: int | None = None
    role: UserRole
    actor_id: int
    module: str | None = None
    event_type: str
    delta: float
    reason: str
    source_ref: str
    ai_suggested: bool
    approved_by_id: int | None = None
    details: dict[str, Any]
    created_at: datetime
    actor: UserSummary | None = None


class RoleScoreRead(ORMModel):
    id: int
    actor_id: int
    role: UserRole
    period: str
    module: str | None = None
    computed_value: float
    breakdown: dict[str, Any]
    start_date: date | None = None
    end_date: date | None = None
    updated_at: datetime
    actor: UserSummary | None = None


class OverviewCard(BaseModel):
    label: str
    value: float | int
    unit: str | None = None
    trend: float | None = None
    context: str | None = None


class OverviewResponse(BaseModel):
    cards: list[OverviewCard]


class ModuleHeatmapItem(BaseModel):
    module: str
    label: str
    story_count: int
    bug_count: int
    defect_density: float
    escaped_defect_rate: float
    severity_index: float
    quality_index: float


class ModuleHeatmapResponse(BaseModel):
    items: list[ModuleHeatmapItem]


class BreakdownItem(BaseModel):
    label: str
    value: float
    count: int
    stories: list[StoryDrilldown] = Field(default_factory=list)


class BugBreakdownResponse(BaseModel):
    module: str
    items: list[BreakdownItem]


class RootCauseBreakdownResponse(BaseModel):
    module: str
    category: str
    items: list[BreakdownItem]


class TrendPoint(BaseModel):
    label: str
    value: float
    escaped_defect_rate: float
    production_defects: int
    story_count: int
    bug_count: int


class TrendResponse(BaseModel):
    items: list[TrendPoint]


class LeaderboardEntry(BaseModel):
    user_id: int
    name: str
    role: UserRole
    score: float
    module: str | None = None
    facts: list[str] = Field(default_factory=list)


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardEntry]


class ChainViewItem(BaseModel):
    origin_stage: DetectionStage
    detected_stage: DetectionStage
    count: int
    weighted_impact: float


class ChainViewResponse(BaseModel):
    items: list[ChainViewItem]


class UserScorecardResponse(BaseModel):
    user: UserRead
    scores: list[RoleScoreRead]
    recent_events: list[QualityEventRead]
