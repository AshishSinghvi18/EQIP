"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.models import (
    BugSeverity,
    BugStatus,
    DetectedStage,
    EventType,
    OriginStage,
    RootCauseCategory,
    StoryStatus,
    UserRole,
)


# --- User ---


class UserCreate(BaseModel):
    email: str
    name: str
    role: UserRole
    team_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    team_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Team ---


class TeamCreate(BaseModel):
    name: str


class TeamResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Project ---


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Sprint ---


class SprintCreate(BaseModel):
    name: str
    project_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SprintResponse(BaseModel):
    id: int
    name: str
    project_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Story ---


class StoryCreate(BaseModel):
    story_id: str
    title: str
    epic: Optional[str] = None
    project_id: int
    sprint_id: Optional[int] = None
    module: Optional[str] = None
    priority: Optional[str] = None
    complexity: Optional[str] = None
    story_points: Optional[int] = None
    acceptance_criteria: Optional[str] = None
    ba_id: Optional[int] = None
    developer_id: Optional[int] = None
    tester_id: Optional[int] = None
    automation_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    status: StoryStatus = StoryStatus.BACKLOG
    estimated_date: Optional[datetime] = None
    release: Optional[str] = None
    environment: Optional[str] = None


class StoryResponse(BaseModel):
    id: int
    story_id: str
    title: str
    epic: Optional[str] = None
    project_id: int
    sprint_id: Optional[int] = None
    module: Optional[str] = None
    priority: Optional[str] = None
    complexity: Optional[str] = None
    story_points: Optional[int] = None
    acceptance_criteria: Optional[str] = None
    ba_id: Optional[int] = None
    developer_id: Optional[int] = None
    tester_id: Optional[int] = None
    automation_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    status: StoryStatus
    estimated_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    release: Optional[str] = None
    environment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Bug ---


class BugCreate(BaseModel):
    bug_id: str
    story_id: Optional[int] = None
    summary: str
    description: Optional[str] = None
    severity: BugSeverity
    priority: Optional[str] = None
    environment: Optional[str] = None
    detected_by: Optional[int] = None
    detected_stage: Optional[DetectedStage] = None
    assigned_to: Optional[int] = None
    root_cause: Optional[str] = None
    root_cause_category: Optional[RootCauseCategory] = None
    origin_stage: Optional[OriginStage] = None
    ownership_split: Optional[dict] = None
    bug_category: Optional[str] = None


class BugResponse(BaseModel):
    id: int
    bug_id: str
    story_id: Optional[int] = None
    summary: str
    description: Optional[str] = None
    severity: BugSeverity
    priority: Optional[str] = None
    environment: Optional[str] = None
    detected_by: Optional[int] = None
    detected_stage: Optional[DetectedStage] = None
    assigned_to: Optional[int] = None
    root_cause: Optional[str] = None
    root_cause_category: Optional[RootCauseCategory] = None
    origin_stage: Optional[OriginStage] = None
    ownership_split: Optional[dict] = None
    bug_category: Optional[str] = None
    resolution: Optional[str] = None
    status: BugStatus
    created_date: datetime
    closed_date: Optional[datetime] = None
    ai_suggested: Optional[dict] = None
    ai_confidence: Optional[float] = None
    human_approved_by: Optional[int] = None
    human_approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Quality Event ---


class QualityEventCreate(BaseModel):
    story_id: Optional[int] = None
    bug_id: Optional[int] = None
    role: UserRole
    actor_id: int
    event_type: EventType
    delta: float
    reason: str
    source_ref: Optional[str] = None
    ai_suggested: bool = False


class QualityEventResponse(BaseModel):
    id: int
    story_id: Optional[int] = None
    bug_id: Optional[int] = None
    role: UserRole
    actor_id: int
    event_type: EventType
    delta: float
    reason: str
    source_ref: Optional[str] = None
    ai_suggested: bool
    approved_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Role Score ---


class RoleScoreResponse(BaseModel):
    id: int
    actor_id: int
    role: UserRole
    period: str
    module: Optional[str] = None
    computed_value: float
    breakdown: Optional[list] = None
    computed_at: datetime

    class Config:
        from_attributes = True


# --- Scoring Weight ---


class ScoringWeightCreate(BaseModel):
    project_id: Optional[int] = None
    event_type: Optional[EventType] = None
    severity: Optional[BugSeverity] = None
    weight: float = 1.0


class ScoringWeightResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    event_type: Optional[EventType] = None
    severity: Optional[BugSeverity] = None
    weight: float
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Import ---


class ImportResult(BaseModel):
    total_rows: int
    imported: int
    errors: list[dict]


# --- Attachment ---


class AttachmentResponse(BaseModel):
    id: int
    story_id: int
    filename: str
    file_type: str
    file_size: int
    description: Optional[str] = None
    uploaded_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Badge ---


class BadgeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    criteria: Optional[dict] = None
    icon: Optional[str] = None


class BadgeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    criteria: Optional[dict] = None
    icon: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserBadgeResponse(BaseModel):
    id: int
    user_id: int
    badge_id: int
    period: str
    evidence: Optional[list] = None
    awarded_at: datetime

    class Config:
        from_attributes = True


# --- Dispute (FR-16) ---


class DisputeCreate(BaseModel):
    bug_id: int
    raised_by: int
    reason: str


class DisputeResolve(BaseModel):
    resolution: str
    resolved_by: int
    status: str = "resolved"  # resolved or rejected


class DisputeResponse(BaseModel):
    id: int
    bug_id: int
    raised_by: int
    reason: str
    status: str
    resolution: Optional[str] = None
    resolved_by: Optional[int] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Coaching (FR-15) ---


class CoachingRecommendationResponse(BaseModel):
    id: int
    user_id: int
    module: Optional[str] = None
    category: str
    recommendation: str
    supporting_data: Optional[dict] = None
    is_dismissed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Forecast (Phase 4) ---


class QualityForecastResponse(BaseModel):
    id: int
    project_id: int
    sprint_id: Optional[int] = None
    release: Optional[str] = None
    risk_score: float
    confidence: float
    factors: Optional[list] = None
    recommendations: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Search ---


class SearchResult(BaseModel):
    entity_type: str  # story, bug, event
    entity_id: int
    title: str
    snippet: str
    relevance_score: float


# --- Embedding (Phase 2) ---


class EmbeddingResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    chunk_text: str
    model_name: str
    has_vector: bool
    created_at: datetime

    class Config:
        from_attributes = True
        protected_namespaces = ()


class BackfillResult(BaseModel):
    stories: int
    bugs: int
    events: int


# --- Full-Chain RCA (Phase 2, FR-6) ---


class RCAChainStage(BaseModel):
    stage: str
    description: str
    responsible_role: str
    status: str  # origin, missed, passed_through, not_applicable
    note: Optional[str] = None


class RCAChainAnalysisResponse(BaseModel):
    id: int
    bug_id: int
    chain_stages: list[dict]
    root_origin_stage: str
    contributing_factors: Optional[list] = None
    ownership_split: Optional[dict] = None
    ai_confidence: Optional[float] = None
    reasoning: Optional[str] = None
    analyzed_by: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChainSummaryResponse(BaseModel):
    total_analyzed: int
    origin_distribution: dict
    common_missed_stages: dict
