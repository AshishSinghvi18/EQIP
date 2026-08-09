"""Core database models for EQIP - Engineering Quality Intelligence Platform."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


# --- Enums ---


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENGINEERING_MANAGER = "engineering_manager"
    DEVELOPER = "developer"
    BUSINESS_ANALYST = "business_analyst"
    TESTER = "tester"
    AUTOMATION_ENGINEER = "automation_engineer"


class StoryStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    IN_TESTING = "in_testing"
    DONE = "done"
    RELEASED = "released"


class BugSeverity(str, enum.Enum):
    INFORMATIONAL = "informational"
    COSMETIC = "cosmetic"
    GENERAL = "general"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    PRODUCTION = "production"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATA_LOSS = "data_loss"


class BugStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    VERIFIED = "verified"
    CLOSED = "closed"
    REOPENED = "reopened"


class RootCauseCategory(str, enum.Enum):
    REQUIREMENT_GAP = "requirement_gap"
    ACCEPTANCE_CRITERIA_MISSING = "acceptance_criteria_missing"
    BUSINESS_LOGIC = "business_logic"
    VALIDATION = "validation"
    UI = "ui"
    API = "api"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    REGRESSION = "regression"
    DEPLOYMENT = "deployment"
    ENVIRONMENT = "environment"
    AUTOMATION_GAP = "automation_gap"
    TESTING_GAP = "testing_gap"
    CUSTOMER_CHANGE = "customer_change"
    UNKNOWN = "unknown"


class BugReasoningClass(str, enum.Enum):
    """Bug-reasoning classes (Design Spec §7.4)."""
    SILLY_MISS = "silly_miss"
    CRITICAL_MISS = "critical_miss"
    INFO_NOT_IN_STORY = "info_not_in_story"
    MISSING_UNIT_TEST = "missing_unit_test"
    WRONG_TEST_CASES = "wrong_test_cases"


class QualityClass(str, enum.Enum):
    """Story quality classification (Design Spec §4.7)."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT_DATA = "insufficient_data"


class OriginStage(str, enum.Enum):
    REQUIREMENT = "requirement"
    DEVELOPMENT = "development"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    AUTOMATION = "automation"
    UAT = "uat"
    RELEASE = "release"
    PRODUCTION = "production"


class DetectedStage(str, enum.Enum):
    CODE_REVIEW = "code_review"
    UNIT_TESTING = "unit_testing"
    INTEGRATION_TESTING = "integration_testing"
    QA_TESTING = "qa_testing"
    UAT = "uat"
    STAGING = "staging"
    PRODUCTION = "production"


class EventType(str, enum.Enum):
    # Developer gains
    FIRST_TIME_RIGHT_REVIEW = "first_time_right_review"
    ZERO_DEFECT_STORY = "zero_defect_story"
    REUSABLE_COMPONENT = "reusable_component"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    SECURITY_IMPROVEMENT = "security_improvement"
    EARLY_COMPLETION = "early_completion"
    # Developer losses
    VALIDATION_BUG = "validation_bug"
    LOGIC_BUG = "logic_bug"
    HIGH_SEVERITY_DEFECT = "high_severity_defect"
    PRODUCTION_DEFECT = "production_defect"
    REWORK_CYCLE = "rework_cycle"
    FAILED_CODE_REVIEW = "failed_code_review"
    # BA gains
    COMPLETE_ACCEPTANCE_CRITERIA = "complete_acceptance_criteria"
    WELL_DOCUMENTED_STORY = "well_documented_story"
    EDGE_CASES_COVERED = "edge_cases_covered"
    LOW_CLARIFICATION_COUNT = "low_clarification_count"
    # BA losses
    REQUIREMENT_GAP_TRACED = "requirement_gap_traced"
    WRONG_FLOW = "wrong_flow"
    MISSING_ACCEPTANCE_CRITERIA = "missing_acceptance_criteria"
    LATE_REQUIREMENT_CHANGE = "late_requirement_change"
    # Tester gains
    CRITICAL_ISSUE_FOUND = "critical_issue_found"
    EDGE_CASE_FOUND = "edge_case_found"
    BOUNDARY_ISSUE_FOUND = "boundary_issue_found"
    SECURITY_ISSUE_FOUND = "security_issue_found"
    PERFORMANCE_ISSUE_FOUND = "performance_issue_found"
    STRONG_REGRESSION_COVERAGE = "strong_regression_coverage"
    # Tester losses
    ESCAPED_PRODUCTION_DEFECT = "escaped_production_defect"
    WEAK_REGRESSION = "weak_regression"
    FALSE_POSITIVE = "false_positive"
    INCOMPLETE_TESTING = "incomplete_testing"
    LATE_TESTING = "late_testing"
    # Automation gains
    REGRESSION_AUTOMATED = "regression_automated"
    STABLE_SCRIPTS = "stable_scripts"
    HIGH_COVERAGE = "high_coverage"
    FAST_EXECUTION = "fast_execution"
    CI_INTEGRATION = "ci_integration"
    # Automation losses
    BROKEN_SCRIPTS = "broken_scripts"
    FLAKY_TESTS = "flaky_tests"
    LOW_COVERAGE = "low_coverage"
    MAINTENANCE_BACKLOG = "maintenance_backlog"
    # Shared ownership adjustment
    SHARED_OWNERSHIP_ADJUSTMENT = "shared_ownership_adjustment"


# --- Models ---


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")
    quality_events = relationship("QualityEvent", foreign_keys="[QualityEvent.actor_id]", back_populates="actor")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("User", back_populates="team")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sprints = relationship("Sprint", back_populates="project")
    stories = relationship("Story", back_populates="project")


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="sprints")
    stories = relationship("Story", back_populates="sprint")


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    epic = Column(String(255), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    module = Column(String(255), nullable=True)
    priority = Column(String(50), nullable=True)
    complexity = Column(String(50), nullable=True)
    story_points = Column(Integer, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    ba_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tester_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    automation_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(StoryStatus), default=StoryStatus.BACKLOG)
    estimated_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    release = Column(String(100), nullable=True)
    environment = Column(String(100), nullable=True)
    documentation = Column(Text, nullable=True)
    # v1.1 onboarding data gate fields (§4.8, §8.1)
    description = Column(Text, nullable=True)
    screenshots = Column(JSON, nullable=True)  # list of screenshot references
    unit_test_cases = Column(JSON, nullable=True)  # from developers
    ba_test_cases = Column(JSON, nullable=True)  # from BA/testers
    escalations = Column(JSON, nullable=True)  # list of escalation records
    onboarding_complete = Column(Boolean, default=False)
    completeness_gaps = Column(JSON, nullable=True)  # list of missing data points
    # v1.1 derived fields (§4.6, §4.7)
    story_rollup = Column(Float, nullable=True)  # avg of role scores, display-only
    quality_class = Column(Enum(QualityClass), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="stories")
    sprint = relationship("Sprint", back_populates="stories")
    bugs = relationship("Bug", back_populates="story")
    attachments_rel = relationship("Attachment", back_populates="story")
    role_story_scores = relationship("PerRoleStoryScore", back_populates="story")
    story_class_record = relationship("StoryClassRecord", back_populates="story", uselist=False)


class Bug(Base):
    __tablename__ = "bugs"

    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(String(100), unique=True, index=True, nullable=False)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    summary = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(BugSeverity), nullable=False)
    priority = Column(String(50), nullable=True)
    environment = Column(String(100), nullable=True)
    detected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    detected_stage = Column(Enum(DetectedStage), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    root_cause = Column(Text, nullable=True)
    root_cause_category = Column(Enum(RootCauseCategory), nullable=True)
    origin_stage = Column(Enum(OriginStage), nullable=True)
    ownership_split = Column(JSON, nullable=True)  # e.g. {"ba": 40, "dev": 40, "tester": 20}
    bug_category = Column(String(100), nullable=True)
    resolution = Column(Text, nullable=True)
    status = Column(Enum(BugStatus), default=BugStatus.OPEN)
    created_date = Column(DateTime, default=datetime.utcnow)
    closed_date = Column(DateTime, nullable=True)
    # AI fields
    ai_suggested = Column(JSON, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    human_approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    human_approved_at = Column(DateTime, nullable=True)
    # v1.1 bug-reasoning class (§7.4, §8.2)
    reasoning_class = Column(Enum(BugReasoningClass), nullable=True)
    reasoning_class_approved = Column(Boolean, default=False)

    story = relationship("Story", back_populates="bugs")


class QualityEvent(Base):
    """Immutable, append-only quality event. The single source of truth for scoring."""

    __tablename__ = "quality_events"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)
    bug_id = Column(Integer, ForeignKey("bugs.id"), nullable=True)
    role = Column(Enum(UserRole), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    delta = Column(Float, nullable=False)  # positive = gain, negative = loss
    reason = Column(Text, nullable=False)
    source_ref = Column(String(255), nullable=True)  # link to bug/review/etc.
    ai_suggested = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    actor = relationship("User", foreign_keys="[QualityEvent.actor_id]", back_populates="quality_events")


class RoleScore(Base):
    """Derived score - recomputed from quality events. Never directly overwritten."""

    __tablename__ = "role_scores"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    period = Column(String(50), nullable=False)  # e.g. "2026-Q3", "2026-07", "sprint-42"
    module = Column(String(255), nullable=True)
    computed_value = Column(Float, nullable=False, default=0.0)
    breakdown = Column(JSON, nullable=True)  # list of contributing event summaries
    computed_at = Column(DateTime, default=datetime.utcnow)


class ScoringWeight(Base):
    """Admin-configurable weights for event types and severities."""

    __tablename__ = "scoring_weights"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    event_type = Column(Enum(EventType), nullable=True)
    severity = Column(Enum(BugSeverity), nullable=True)
    weight = Column(Float, nullable=False, default=1.0)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Attachment(Base):
    """Reference documents attached to stories (Word/PDF/Excel)."""

    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, xlsx, csv
    file_size = Column(Integer, nullable=False)  # bytes
    file_path = Column(String(1000), nullable=False)  # storage path
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("Story", back_populates="attachments_rel")


class Badge(Base):
    """Badges awarded based on quality facts (FR-14)."""

    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # e.g. "Zero-Bug Champion"
    description = Column(Text, nullable=True)
    criteria = Column(JSON, nullable=True)  # rules for earning this badge
    icon = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserBadge(Base):
    """Badge awards to users with supporting evidence (FR-14)."""

    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    period = Column(String(50), nullable=False)  # e.g. "2026-07"
    evidence = Column(JSON, nullable=True)  # facts behind the badge
    awarded_at = Column(DateTime, default=datetime.utcnow)


class Dispute(Base):
    """Dispute handling for AI-assigned root cause/owner (FR-16)."""

    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(Integer, ForeignKey("bugs.id"), nullable=False)
    raised_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="open")  # open, resolved, rejected
    resolution = Column(Text, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class CoachingRecommendation(Base):
    """AI-generated coaching recommendations (FR-15)."""

    __tablename__ = "coaching_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False)  # area of improvement
    recommendation = Column(Text, nullable=False)
    supporting_data = Column(JSON, nullable=True)  # facts behind the tip
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Embedding(Base):
    """Vector embeddings for semantic search (Design Spec §8.5, FR-10).

    Stores text chunks with their vector representation for pgvector similarity search.
    Dimension follows the embedding model (1024 for BGE-M3).
    """

    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # story, bug, event
    entity_id = Column(Integer, nullable=False, index=True)
    chunk_text = Column(Text, nullable=False)
    # Vector stored as JSON array for SQLite compatibility; in production with
    # PostgreSQL + pgvector, this would be a Vector(1024) column.
    vector = Column(JSON, nullable=True)
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RCAChainAnalysis(Base):
    """Full-chain root cause analysis record (Design Spec §5, FR-6).

    Traces a defect through the full delivery chain and records the analysis.
    """

    __tablename__ = "rca_chain_analyses"

    id = Column(Integer, primary_key=True, index=True)
    bug_id = Column(Integer, ForeignKey("bugs.id"), nullable=False, index=True)
    chain_stages = Column(JSON, nullable=False)  # ordered list of chain stage analyses
    root_origin_stage = Column(Enum(OriginStage), nullable=False)
    contributing_factors = Column(JSON, nullable=True)  # factors at each stage
    ownership_split = Column(JSON, nullable=True)  # percentage per role
    ai_confidence = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    analyzed_by = Column(String(50), default="ai")  # "ai" or "human"
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bug = relationship("Bug")


class QualityForecast(Base):
    """Release-risk prediction and quality forecast (Phase 4)."""

    __tablename__ = "quality_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    release = Column(String(100), nullable=True)
    risk_score = Column(Float, nullable=False)  # 0-100
    confidence = Column(Float, nullable=False)  # 0-1
    factors = Column(JSON, nullable=True)  # contributing risk factors
    recommendations = Column(JSON, nullable=True)  # mitigation actions
    created_at = Column(DateTime, default=datetime.utcnow)


class PerRoleStoryScore(Base):
    """Per-role story score (Design Spec §4.6, §8.6).

    One row per participating role per story. Each role starts at 10.0 and
    loses points only for their own attributed faults. Never overwritten;
    replayable from quality events.
    """

    __tablename__ = "per_role_story_scores"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Float, nullable=False, default=10.0)  # 0.0–10.0
    breakdown = Column(JSON, nullable=True)  # list of deductions on this story
    computed_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("Story", back_populates="role_story_scores")


class StoryClassRecord(Base):
    """Story classification record (Design Spec §4.7, §8.6b).

    Derived from escalation/serious-bug gates and per-role score rollup.
    """

    __tablename__ = "story_class_records"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, unique=True, index=True)
    quality_class = Column(Enum(QualityClass), nullable=False)
    rollup = Column(Float, nullable=True)  # avg of role scores, display-only
    serious_bug_count = Column(Integer, default=0)
    escalation_count = Column(Integer, default=0)
    computed_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("Story", back_populates="story_class_record")
