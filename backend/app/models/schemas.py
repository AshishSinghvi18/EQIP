from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    ENGINEERING_MANAGER = "Engineering Manager"
    DEVELOPER = "Developer"
    BUSINESS_ANALYST = "Business Analyst"
    TESTER = "Tester"
    AUTOMATION_ENGINEER = "Automation Engineer"


class RootCauseCategory(str, enum.Enum):
    REQUIREMENT_GAP = "Requirement gap"
    ACCEPTANCE_CRITERIA_MISSING = "Acceptance-criteria missing"
    BUSINESS_LOGIC = "Business logic"
    VALIDATION = "Validation"
    UI = "UI"
    API = "API"
    DATABASE = "Database"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    REGRESSION = "Regression"
    DEPLOYMENT = "Deployment"
    ENVIRONMENT = "Environment"
    AUTOMATION_GAP = "Automation gap"
    TESTING_GAP = "Testing gap"
    CUSTOMER_CHANGE = "Customer change"
    UNKNOWN = "Unknown"


class SeverityLevel(str, enum.Enum):
    INFORMATIONAL = "Informational"
    COSMETIC = "Cosmetic"
    GENERAL = "General"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
    PRODUCTION = "Production"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    DATA_LOSS = "Data loss"


class DetectionStage(str, enum.Enum):
    REQUIREMENT = "Requirement"
    DEVELOPMENT = "Development"
    CODE_REVIEW = "Code Review"
    TESTING = "Testing"
    AUTOMATION = "Automation"
    UAT = "UAT"
    RELEASE = "Release"
    PRODUCTION = "Production"


class StoryStatus(str, enum.Enum):
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    TESTING = "Testing"
    DONE = "Done"
    RELEASED = "Released"
    BLOCKED = "Blocked"
    CANCELLED = "Cancelled"


class BugStatus(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REJECTED = "Rejected"


class SprintStatus(str, enum.Enum):
    PLANNED = "Planned"
    ACTIVE = "Active"
    CLOSED = "Closed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, native_enum=False), nullable=False, index=True)
    team: Mapped[str | None] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    authored_stories: Mapped[list[Story]] = relationship(back_populates="ba", foreign_keys="Story.ba_id")
    developed_stories: Mapped[list[Story]] = relationship(back_populates="developer", foreign_keys="Story.developer_id")
    tested_stories: Mapped[list[Story]] = relationship(back_populates="tester", foreign_keys="Story.tester_id")
    automated_stories: Mapped[list[Story]] = relationship(back_populates="automation_engineer", foreign_keys="Story.automation_id")
    reviewed_stories: Mapped[list[Story]] = relationship(back_populates="reviewer", foreign_keys="Story.reviewer_id")
    detected_bugs: Mapped[list[Bug]] = relationship(back_populates="detected_by", foreign_keys="Bug.detected_by_id")
    assigned_bugs: Mapped[list[Bug]] = relationship(back_populates="assigned_to", foreign_keys="Bug.assigned_to_id")
    approved_bugs: Mapped[list[Bug]] = relationship(back_populates="human_approved_by", foreign_keys="Bug.human_approved_by_id")
    quality_events: Mapped[list[QualityEvent]] = relationship(back_populates="actor", foreign_keys="QualityEvent.actor_id")
    approved_events: Mapped[list[QualityEvent]] = relationship(back_populates="approved_by", foreign_keys="QualityEvent.approved_by_id")
    role_scores: Mapped[list[RoleScore]] = relationship(back_populates="actor")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="Active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    sprints: Mapped[list[Sprint]] = relationship(back_populates="project", cascade="all, delete-orphan")
    stories: Mapped[list[Story]] = relationship(back_populates="project")
    bugs: Mapped[list[Bug]] = relationship(back_populates="project")


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    goal: Mapped[str | None] = mapped_column(Text)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    release_name: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[SprintStatus] = mapped_column(SQLEnum(SprintStatus, native_enum=False), default=SprintStatus.PLANNED, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="sprints")
    stories: Mapped[list[Story]] = relationship(back_populates="sprint")
    bugs: Mapped[list[Bug]] = relationship(back_populates="sprint")


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    story_key: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    epic: Mapped[str | None] = mapped_column(String(255))
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    sprint_id: Mapped[int] = mapped_column(ForeignKey("sprints.id"), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    priority: Mapped[str | None] = mapped_column(String(50))
    complexity: Mapped[str | None] = mapped_column(String(50))
    story_points: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text)
    ba_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    developer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    tester_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    automation_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[StoryStatus] = mapped_column(SQLEnum(StoryStatus, native_enum=False), default=StoryStatus.DRAFT, nullable=False, index=True)
    estimated_date: Mapped[date | None] = mapped_column(Date)
    completion_date: Mapped[date | None] = mapped_column(Date)
    release_name: Mapped[str | None] = mapped_column(String(120))
    environment: Mapped[str | None] = mapped_column(String(80))
    attachments: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    documentation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="stories")
    sprint: Mapped[Sprint] = relationship(back_populates="stories")
    ba: Mapped[User | None] = relationship(back_populates="authored_stories", foreign_keys=[ba_id])
    developer: Mapped[User | None] = relationship(back_populates="developed_stories", foreign_keys=[developer_id])
    tester: Mapped[User | None] = relationship(back_populates="tested_stories", foreign_keys=[tester_id])
    automation_engineer: Mapped[User | None] = relationship(back_populates="automated_stories", foreign_keys=[automation_id])
    reviewer: Mapped[User | None] = relationship(back_populates="reviewed_stories", foreign_keys=[reviewer_id])
    bugs: Mapped[list[Bug]] = relationship(back_populates="story", cascade="all, delete-orphan")
    quality_events: Mapped[list[QualityEvent]] = relationship(back_populates="story")


class Bug(Base):
    __tablename__ = "bugs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bug_key: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    sprint_id: Mapped[int] = mapped_column(ForeignKey("sprints.id"), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[SeverityLevel] = mapped_column(SQLEnum(SeverityLevel, native_enum=False), nullable=False, index=True)
    priority: Mapped[str | None] = mapped_column(String(50))
    environment: Mapped[str | None] = mapped_column(String(80))
    detected_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    detected_stage: Mapped[DetectionStage] = mapped_column(SQLEnum(DetectionStage, native_enum=False), nullable=False, index=True)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    root_cause: Mapped[str | None] = mapped_column(Text)
    root_cause_category: Mapped[RootCauseCategory] = mapped_column(SQLEnum(RootCauseCategory, native_enum=False), nullable=False, index=True)
    origin_stage: Mapped[DetectionStage] = mapped_column(SQLEnum(DetectionStage, native_enum=False), nullable=False, index=True)
    ownership_split: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    bug_category: Mapped[str | None] = mapped_column(String(120))
    resolution: Mapped[str | None] = mapped_column(Text)
    status: Mapped[BugStatus] = mapped_column(SQLEnum(BugStatus, native_enum=False), default=BugStatus.OPEN, nullable=False, index=True)
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    closed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_suggested: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    human_approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    human_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    story: Mapped[Story] = relationship(back_populates="bugs")
    project: Mapped[Project] = relationship(back_populates="bugs")
    sprint: Mapped[Sprint] = relationship(back_populates="bugs")
    detected_by: Mapped[User | None] = relationship(back_populates="detected_bugs", foreign_keys=[detected_by_id])
    assigned_to: Mapped[User | None] = relationship(back_populates="assigned_bugs", foreign_keys=[assigned_to_id])
    human_approved_by: Mapped[User | None] = relationship(back_populates="approved_bugs", foreign_keys=[human_approved_by_id])
    quality_events: Mapped[list[QualityEvent]] = relationship(back_populates="bug")


class QualityEvent(Base):
    __tablename__ = "quality_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    story_id: Mapped[int | None] = mapped_column(ForeignKey("stories.id"), index=True)
    bug_id: Mapped[int | None] = mapped_column(ForeignKey("bugs.id"), index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), index=True)
    sprint_id: Mapped[int | None] = mapped_column(ForeignKey("sprints.id"), index=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, native_enum=False), nullable=False, index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    module: Mapped[str | None] = mapped_column(String(100), index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    story: Mapped[Story | None] = relationship(back_populates="quality_events")
    bug: Mapped[Bug | None] = relationship(back_populates="quality_events")
    actor: Mapped[User] = relationship(back_populates="quality_events", foreign_keys=[actor_id])
    approved_by: Mapped[User | None] = relationship(back_populates="approved_events", foreign_keys=[approved_by_id])


class RoleScore(Base):
    __tablename__ = "role_scores"
    __table_args__ = (UniqueConstraint("actor_id", "role", "period", "module", name="uq_role_score_scope"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, native_enum=False), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(50), nullable=False, default="all-time")
    module: Mapped[str | None] = mapped_column(String(100))
    computed_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    actor: Mapped[User] = relationship(back_populates="role_scores")
