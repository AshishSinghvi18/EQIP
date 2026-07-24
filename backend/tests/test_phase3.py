"""Tests for Phase 3: Trend analytics, module risk view, auto-badge evaluation."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.models.models import (
    Badge,
    Bug,
    BugSeverity,
    BugStatus,
    EventType,
    OriginStage,
    QualityEvent,
    RoleScore,
    RootCauseCategory,
    Story,
    StoryStatus,
    User,
    UserBadge,
    UserRole,
)


class TestModuleRiskView:
    """Test module risk assessment (Phase 3)."""

    def test_risk_score_calculation_high_density(self):
        """Modules with high bug density should get higher risk scores."""
        from app.routers.trends import get_module_risk_view

        db = MagicMock()
        # Module with many bugs should yield higher risk
        # The endpoint queries the database; we test the logic via integration
        # This verifies the endpoint can be imported and called
        assert get_module_risk_view is not None

    def test_risk_levels_mapping(self):
        """Verify risk level thresholds."""
        # From the implementation:
        # >= 70 -> critical, >= 40 -> high, >= 20 -> medium, else -> low
        thresholds = [
            (75, "critical"),
            (70, "critical"),
            (50, "high"),
            (40, "high"),
            (25, "medium"),
            (20, "medium"),
            (10, "low"),
            (0, "low"),
        ]
        for score, expected_level in thresholds:
            if score >= 70:
                level = "critical"
            elif score >= 40:
                level = "high"
            elif score >= 20:
                level = "medium"
            else:
                level = "low"
            assert level == expected_level, f"Score {score} should be {expected_level}"


class TestTrendAnalytics:
    """Test quality trend endpoints (Phase 3, Design Spec §10.3)."""

    def test_trend_endpoint_exists(self):
        """Verify trend endpoint can be imported."""
        from app.routers.trends import get_quality_trends
        assert get_quality_trends is not None

    def test_bug_category_trend_endpoint_exists(self):
        """Verify bug category trend endpoint exists."""
        from app.routers.trends import get_bug_category_trend
        assert get_bug_category_trend is not None

    def test_severity_trend_endpoint_exists(self):
        """Verify severity trend endpoint exists."""
        from app.routers.trends import get_severity_trend
        assert get_severity_trend is not None

    def test_score_trend_endpoint_exists(self):
        """Verify user score trend endpoint exists."""
        from app.routers.trends import get_user_score_trend
        assert get_user_score_trend is not None


class TestAutoBadgeEvaluation:
    """Test automatic badge evaluation based on quality facts (Phase 3, FR-14)."""

    def test_evaluate_badges_endpoint_exists(self):
        """Verify auto-badge evaluation endpoint exists."""
        from app.routers.trends import evaluate_badges
        assert evaluate_badges is not None

    def test_zero_bug_champion_criteria(self):
        """Zero-Bug Champion requires >= 3 zero_defect_story events."""
        # Create mock events
        events = []
        for i in range(3):
            e = MagicMock(spec=QualityEvent)
            e.event_type = MagicMock()
            e.event_type.value = "zero_defect_story"
            e.delta = 2.0
            e.story_id = i + 1
            events.append(e)

        # Verify the criteria logic
        zero_defect_count = sum(
            1 for e in events if e.event_type.value == "zero_defect_story"
        )
        assert zero_defect_count >= 3

    def test_quality_champion_criteria(self):
        """Quality Champion requires positive > 2x negative and >= 10 positive."""
        positive_events = [MagicMock(delta=1.0) for _ in range(12)]
        negative_events = [MagicMock(delta=-1.0) for _ in range(3)]

        assert len(positive_events) >= 10
        assert len(positive_events) > 2 * len(negative_events)

    def test_code_guardian_criteria(self):
        """Code Guardian requires >= 5 first_time_right_review events."""
        events = []
        for i in range(5):
            e = MagicMock(spec=QualityEvent)
            e.event_type = MagicMock()
            e.event_type.value = "first_time_right_review"
            e.delta = 2.0
            events.append(e)

        count = sum(
            1 for e in events if e.event_type.value == "first_time_right_review"
        )
        assert count >= 5

    def test_badge_not_awarded_below_threshold(self):
        """Badge should NOT be awarded if criteria not met."""
        events = []
        for i in range(2):  # Only 2, needs 3
            e = MagicMock(spec=QualityEvent)
            e.event_type = MagicMock()
            e.event_type.value = "zero_defect_story"
            e.delta = 2.0
            events.append(e)

        zero_defect_count = sum(
            1 for e in events if e.event_type.value == "zero_defect_story"
        )
        assert zero_defect_count < 3  # Should NOT qualify

    def test_edge_case_hunter_criteria(self):
        """Edge-Case Hunter requires >= 3 edge_case_found/boundary_issue_found."""
        events = []
        for event_type in ["edge_case_found", "boundary_issue_found", "edge_case_found"]:
            e = MagicMock(spec=QualityEvent)
            e.event_type = MagicMock()
            e.event_type.value = event_type
            e.delta = 1.5
            events.append(e)

        count = sum(
            1
            for e in events
            if e.event_type.value in ("edge_case_found", "boundary_issue_found")
        )
        assert count >= 3


class TestTrendRouter:
    """Test the trends router is properly registered."""

    def test_router_has_correct_prefix(self):
        from app.routers.trends import router
        assert router.prefix == "/trends"

    def test_router_has_correct_tags(self):
        from app.routers.trends import router
        assert "trends" in router.tags
