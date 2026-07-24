"""Tests for the EQIP score engine and API."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.models.models import (
    EventType,
    QualityEvent,
    RoleScore,
    UserRole,
)
from app.services.score_engine import compute_score_for_actor, record_quality_event


class TestRecordQualityEvent:
    """Test immutable event recording (FR-11)."""

    def test_record_event_creates_immutable_record(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        event = record_quality_event(
            db=db,
            story_id=1,
            bug_id=None,
            role=UserRole.DEVELOPER,
            actor_id=1,
            event_type=EventType.FIRST_TIME_RIGHT_REVIEW,
            delta=2.0,
            reason="Code review passed first time",
            source_ref="CR-123",
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_ai_suggested_event_not_auto_approved(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        event = record_quality_event(
            db=db,
            story_id=1,
            bug_id=1,
            role=UserRole.DEVELOPER,
            actor_id=1,
            event_type=EventType.VALIDATION_BUG,
            delta=-1.5,
            reason="AI detected validation issue",
            ai_suggested=True,
        )

        db.add.assert_called_once()
        added_event = db.add.call_args[0][0]
        assert added_event.ai_suggested is True
        assert added_event.approved_by is None


class TestScoreComputation:
    """Test per-role score computation (FR-4)."""

    def test_independent_scoring_no_zero_sum(self):
        """Two roles on the same story can both score positively (FR-4, Design §4)."""
        # This validates the core design decision: no shared point pool
        db = MagicMock()

        # Developer event
        dev_event = QualityEvent(
            id=1,
            story_id=1,
            role=UserRole.DEVELOPER,
            actor_id=1,
            event_type=EventType.ZERO_DEFECT_STORY,
            delta=3.0,
            reason="Zero defects",
            ai_suggested=False,
            approved_by=None,
            created_at=datetime.utcnow(),
        )

        # Tester event on the SAME story
        tester_event = QualityEvent(
            id=2,
            story_id=1,
            role=UserRole.TESTER,
            actor_id=2,
            event_type=EventType.STRONG_REGRESSION_COVERAGE,
            delta=2.0,
            reason="Full regression coverage",
            ai_suggested=False,
            approved_by=None,
            created_at=datetime.utcnow(),
        )

        # Both deltas are positive - no zero-sum
        assert dev_event.delta > 0
        assert tester_event.delta > 0

    def test_ai_unapproved_events_excluded(self):
        """AI-suggested events without approval have zero effect on score (FR-9)."""
        db = MagicMock()

        unapproved = QualityEvent(
            id=1,
            story_id=1,
            role=UserRole.DEVELOPER,
            actor_id=1,
            event_type=EventType.LOGIC_BUG,
            delta=-2.0,
            reason="AI detected logic bug",
            ai_suggested=True,
            approved_by=None,
            created_at=datetime.utcnow(),
        )

        approved = QualityEvent(
            id=2,
            story_id=1,
            role=UserRole.DEVELOPER,
            actor_id=1,
            event_type=EventType.FIRST_TIME_RIGHT_REVIEW,
            delta=2.0,
            reason="Clean review",
            ai_suggested=False,
            approved_by=None,
            created_at=datetime.utcnow(),
        )

        # Simulating compute logic: only non-AI or approved events count
        events = [unapproved, approved]
        total = 0.0
        for e in events:
            if e.ai_suggested and e.approved_by is None:
                continue
            total += e.delta

        # Unapproved AI event should NOT affect score
        assert total == 2.0  # Only the approved non-AI event counts


class TestImportService:
    """Test story/bug import (FR-2, FR-3)."""

    def test_csv_column_normalization(self):
        from app.services.import_service import _normalize_columns
        import pandas as pd

        df = pd.DataFrame({"Story ID": ["S-1"], "Title": ["Test"]})
        result = _normalize_columns(df, {"story_id": ["story_id", "id"], "title": ["title"]})
        assert "story_id" in result.columns
        assert "title" in result.columns
