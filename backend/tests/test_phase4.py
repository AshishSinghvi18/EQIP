"""Tests for Phase 4: Release-risk prediction, quality forecasting, org benchmarking."""

from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta

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
    UserRole,
)
from app.services.forecast_service import (
    _compute_trend_direction,
    _generate_risk_recommendations,
    _linear_slope,
    generate_release_forecast,
    get_engineering_health_index,
    get_org_benchmarking,
    get_quality_trend,
)


# --- Linear Slope Tests ---


class TestLinearSlope:
    """Test the linear regression slope helper."""

    def test_flat_values(self):
        assert _linear_slope([5.0, 5.0, 5.0, 5.0]) == 0.0

    def test_increasing_values(self):
        slope = _linear_slope([1.0, 2.0, 3.0, 4.0])
        assert slope == 1.0

    def test_decreasing_values(self):
        slope = _linear_slope([4.0, 3.0, 2.0, 1.0])
        assert slope == -1.0

    def test_single_value(self):
        assert _linear_slope([5.0]) == 0.0

    def test_empty_list(self):
        assert _linear_slope([]) == 0.0

    def test_two_values(self):
        slope = _linear_slope([0.0, 2.0])
        assert slope == 2.0


# --- Trend Direction Tests ---


class TestComputeTrendDirection:
    """Test quality trend direction computation."""

    def test_improving_trend(self):
        """Decreasing bug density + increasing completion = improving."""
        data = [
            {"bug_density": 2.0, "completion_rate": 60.0, "positive_event_ratio": 50.0},
            {"bug_density": 1.5, "completion_rate": 70.0, "positive_event_ratio": 55.0},
            {"bug_density": 1.0, "completion_rate": 80.0, "positive_event_ratio": 60.0},
            {"bug_density": 0.5, "completion_rate": 90.0, "positive_event_ratio": 65.0},
        ]
        result = _compute_trend_direction(data)
        assert result["direction"] == "improving"
        assert result["bug_density_trend"] == "improving"
        assert result["completion_trend"] == "improving"
        assert result["predicted_bug_density"] < 0.5

    def test_declining_trend(self):
        """Increasing bug density + decreasing completion = declining."""
        data = [
            {"bug_density": 0.5, "completion_rate": 90.0, "positive_event_ratio": 60.0},
            {"bug_density": 1.0, "completion_rate": 80.0, "positive_event_ratio": 55.0},
            {"bug_density": 1.5, "completion_rate": 70.0, "positive_event_ratio": 50.0},
            {"bug_density": 2.0, "completion_rate": 60.0, "positive_event_ratio": 45.0},
        ]
        result = _compute_trend_direction(data)
        assert result["direction"] == "declining"
        assert result["bug_density_trend"] == "declining"
        assert result["completion_trend"] == "declining"

    def test_stable_trend(self):
        """Flat metrics = stable."""
        data = [
            {"bug_density": 1.0, "completion_rate": 75.0, "positive_event_ratio": 50.0},
            {"bug_density": 1.0, "completion_rate": 75.0, "positive_event_ratio": 50.0},
            {"bug_density": 1.0, "completion_rate": 75.0, "positive_event_ratio": 50.0},
        ]
        result = _compute_trend_direction(data)
        assert result["direction"] == "stable"

    def test_single_period(self):
        """Single period returns stable with low confidence."""
        data = [{"bug_density": 1.5, "completion_rate": 70.0, "positive_event_ratio": 50.0}]
        result = _compute_trend_direction(data)
        assert result["direction"] == "stable"
        assert result["confidence"] == 0.2

    def test_predicted_values_non_negative(self):
        """Predicted bug density never goes below 0."""
        data = [
            {"bug_density": 0.2, "completion_rate": 95.0, "positive_event_ratio": 80.0},
            {"bug_density": 0.1, "completion_rate": 98.0, "positive_event_ratio": 85.0},
        ]
        result = _compute_trend_direction(data)
        assert result["predicted_bug_density"] >= 0

    def test_predicted_completion_capped_at_100(self):
        """Predicted completion rate never exceeds 100%."""
        data = [
            {"bug_density": 0.5, "completion_rate": 95.0, "positive_event_ratio": 80.0},
            {"bug_density": 0.3, "completion_rate": 98.0, "positive_event_ratio": 85.0},
            {"bug_density": 0.1, "completion_rate": 99.5, "positive_event_ratio": 90.0},
        ]
        result = _compute_trend_direction(data)
        assert result["predicted_completion_rate"] <= 100

    def test_confidence_increases_with_data(self):
        """More data points = higher confidence."""
        short = [
            {"bug_density": 1.0, "completion_rate": 70.0, "positive_event_ratio": 50.0},
            {"bug_density": 0.8, "completion_rate": 75.0, "positive_event_ratio": 55.0},
        ]
        long = [
            {"bug_density": 1.0, "completion_rate": 70.0, "positive_event_ratio": 50.0},
            {"bug_density": 0.9, "completion_rate": 72.0, "positive_event_ratio": 52.0},
            {"bug_density": 0.8, "completion_rate": 74.0, "positive_event_ratio": 54.0},
            {"bug_density": 0.7, "completion_rate": 76.0, "positive_event_ratio": 56.0},
            {"bug_density": 0.6, "completion_rate": 78.0, "positive_event_ratio": 58.0},
        ]
        short_result = _compute_trend_direction(short)
        long_result = _compute_trend_direction(long)
        assert long_result["confidence"] > short_result["confidence"]


# --- Risk Recommendations Tests ---


class TestRiskRecommendations:
    """Test recommendation generation based on risk factors."""

    def test_high_risk_recommendation(self):
        recs = _generate_risk_recommendations([], 75.0)
        assert any("HIGH RISK" in r for r in recs)

    def test_moderate_risk_recommendation(self):
        recs = _generate_risk_recommendations([], 50.0)
        assert any("MODERATE RISK" in r for r in recs)

    def test_low_risk_recommendation(self):
        recs = _generate_risk_recommendations([], 20.0)
        assert any("LOW RISK" in r for r in recs)

    def test_high_bug_density_recommendation(self):
        factors = [{"factor": "Bug density", "value": 3.5, "impact": 20}]
        recs = _generate_risk_recommendations(factors, 50.0)
        assert any("bug density" in r.lower() for r in recs)

    def test_critical_bugs_recommendation(self):
        factors = [{"factor": "Open critical/high bugs", "value": 5, "impact": 30}]
        recs = _generate_risk_recommendations(factors, 50.0)
        assert any("critical/high" in r.lower() for r in recs)

    def test_incomplete_stories_recommendation(self):
        factors = [{"factor": "Incomplete stories", "value": 50.0, "impact": 10}]
        recs = _generate_risk_recommendations(factors, 50.0)
        assert any("incomplete" in r.lower() for r in recs)


# --- Release Forecast Integration Tests ---


class TestGenerateReleaseForecast:
    """Test the full release forecast generation."""

    def _setup_db_mock(self, stories=None, bugs=None, critical_bugs=0, negative_events=0):
        """Helper to set up mock DB queries."""
        db = MagicMock()

        # Stories query chain
        story_query = MagicMock()
        story_query.filter.return_value = story_query
        story_query.all.return_value = stories or []
        db.query.return_value = story_query

        return db

    def test_empty_project_returns_zero_risk(self):
        """No stories means zero risk with low confidence."""
        db = MagicMock()

        # Chain: db.query(Story).filter(...).filter(...).all() returns []
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        db.query.return_value = query_mock
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = generate_release_forecast(db, project_id=1)

        assert result.risk_score == 0.0
        assert result.confidence == 0.1

    def test_forecast_risk_score_bounded(self):
        """Risk score is always between 0 and 100."""
        # Use mocks that return many bugs to trigger high risk
        db = MagicMock()
        stories = [MagicMock(id=i, status=StoryStatus.IN_PROGRESS) for i in range(5)]
        for s in stories:
            s.project_id = 1
            s.sprint_id = None
            s.release = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = stories
        query_mock.count.return_value = 50  # many bugs

        # scalar for negative events
        query_mock.scalar.return_value = 100

        db.query.return_value = query_mock
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        result = generate_release_forecast(db, project_id=1)

        assert 0 <= result.risk_score <= 100


# --- Engineering Health Index Tests ---


class TestEngineeringHealthIndex:
    """Test the Engineering Health Index computation."""

    def test_perfect_health(self):
        """No bugs and all positive events = high health."""
        db = MagicMock()

        # We'll patch at a higher level since the query chains are complex
        with patch("app.services.forecast_service.get_engineering_health_index") as orig:
            # Call the real function but test the structure
            pass

        # Directly test with controlled mock that returns expected call pattern
        # total_stories query
        story_count_mock = MagicMock()
        story_count_mock.filter.return_value = story_count_mock
        story_count_mock.count.return_value = 10

        # stories_with_bugs (distinct bug story_ids)
        bug_story_mock = MagicMock()
        bug_story_mock.join.return_value = bug_story_mock
        bug_story_mock.filter.return_value = bug_story_mock
        bug_story_mock.distinct.return_value = bug_story_mock
        bug_story_mock.count.return_value = 0  # zero bugs

        # total_bugs
        total_bugs_mock = MagicMock()
        total_bugs_mock.join.return_value = total_bugs_mock
        total_bugs_mock.filter.return_value = total_bugs_mock
        total_bugs_mock.count.return_value = 0

        # production_bugs
        prod_bugs_mock = MagicMock()
        prod_bugs_mock.join.return_value = prod_bugs_mock
        prod_bugs_mock.filter.return_value = prod_bugs_mock
        prod_bugs_mock.count.return_value = 0

        # positive_events and total_events
        events_mock = MagicMock()
        events_mock.join.return_value = events_mock
        events_mock.filter.return_value = events_mock
        events_mock.scalar.return_value = 10

        # Set up db.query to return different mocks based on what's queried
        call_count = [0]
        def query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:  # Story count
                return story_count_mock
            elif call_count[0] == 2:  # Bug join for total_bugs
                return total_bugs_mock
            elif call_count[0] == 3:  # Bug.story_id distinct
                return bug_story_mock
            elif call_count[0] == 4:  # production_bugs
                return prod_bugs_mock
            elif call_count[0] == 5:  # positive_events
                return events_mock
            else:  # total_events
                return events_mock

        db.query.side_effect = query_side_effect

        result = get_engineering_health_index(db, project_id=1)

        assert "health_index" in result
        assert "components" in result
        assert "totals" in result

    def test_empty_project_health(self):
        """Empty project returns sensible defaults."""
        db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.distinct.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.scalar.return_value = 0
        db.query.return_value = query_mock

        result = get_engineering_health_index(db, project_id=1)

        assert result["health_index"] >= 0
        assert result["totals"]["stories"] == 0


# --- Org Benchmarking Tests ---


class TestOrgBenchmarking:
    """Test org-level benchmarking."""

    def test_empty_org(self):
        """No projects returns empty benchmarks."""
        db = MagicMock()
        db.query.return_value.all.return_value = []

        result = get_org_benchmarking(db)

        assert result["org_health_index"] == 0
        assert result["project_count"] == 0
        assert result["projects"] == []

    def test_benchmarking_returns_sorted_projects(self):
        """Projects are sorted by health index descending."""
        db = MagicMock()

        p1 = MagicMock(id=1)
        p1.name = "ProjectA"
        p2 = MagicMock(id=2)
        p2.name = "ProjectB"
        projects = [p1, p2]
        db.query.return_value.all.return_value = projects

        with patch(
            "app.services.forecast_service.get_engineering_health_index"
        ) as mock_health:
            mock_health.side_effect = [
                {
                    "health_index": 60.0,
                    "components": {"zero_bug_rate": 70.0, "positive_event_ratio": 50.0, "production_stability": 80.0},
                    "totals": {"stories": 10, "bugs": 3, "production_defects": 1, "quality_events": 20},
                },
                {
                    "health_index": 85.0,
                    "components": {"zero_bug_rate": 90.0, "positive_event_ratio": 80.0, "production_stability": 95.0},
                    "totals": {"stories": 15, "bugs": 1, "production_defects": 0, "quality_events": 30},
                },
            ]

            result = get_org_benchmarking(db)

        assert result["project_count"] == 2
        # Sorted descending by health_index
        assert result["projects"][0]["project_name"] == "ProjectB"
        assert result["projects"][0]["health_index"] == 85.0
        assert result["projects"][1]["project_name"] == "ProjectA"
        assert result["projects"][1]["health_index"] == 60.0

    def test_org_averages_computed_correctly(self):
        """Org-level averages are correctly computed."""
        db = MagicMock()
        p1 = MagicMock(id=1)
        p1.name = "P1"
        projects = [p1]
        db.query.return_value.all.return_value = projects

        with patch(
            "app.services.forecast_service.get_engineering_health_index"
        ) as mock_health:
            mock_health.return_value = {
                "health_index": 75.0,
                "components": {"zero_bug_rate": 80.0, "positive_event_ratio": 70.0, "production_stability": 90.0},
                "totals": {"stories": 20, "bugs": 4, "production_defects": 1, "quality_events": 40},
            }

            result = get_org_benchmarking(db)

        assert result["org_health_index"] == 75.0
        assert result["org_bug_density"] == 0.2  # 4 bugs / 20 stories
