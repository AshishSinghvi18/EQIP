"""Tests for v1.1 features: per-role story scores, story classification,
onboarding data gate, and bug-reasoning classes (FR-18 to FR-22, §4.6–§4.8, §7.4)."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

from app.models.models import (
    Bug,
    BugReasoningClass,
    BugSeverity,
    BugStatus,
    QualityClass,
    PerRoleStoryScore,
    Story,
    StoryClassRecord,
    StoryStatus,
    UserRole,
)
from app.services.story_score_engine import (
    check_onboarding_completeness,
    _normalize_role,
    DEFAULT_DEDUCTIONS,
    SERIOUS_SEVERITIES,
)
from app.services.ai_service import (
    _keyword_suggest_reasoning_class,
    suggest_bug_reasoning_class,
    REASONING_CLASS_KEYWORDS,
)


class TestOnboardingDataGate:
    """Test onboarding completeness check (§4.8, FR-18)."""

    def test_story_with_all_data_is_complete(self):
        story = MagicMock(spec=Story)
        story.description = "Full description"
        story.acceptance_criteria = "AC text"
        story.unit_test_cases = ["test1", "test2"]
        story.ba_test_cases = ["scenario1"]

        is_complete, gaps = check_onboarding_completeness(story)
        assert is_complete is True
        assert gaps == []

    def test_story_missing_description_has_gap(self):
        story = MagicMock(spec=Story)
        story.description = None
        story.acceptance_criteria = None
        story.unit_test_cases = ["test1"]
        story.ba_test_cases = ["scenario1"]

        is_complete, gaps = check_onboarding_completeness(story)
        assert is_complete is False
        assert "story_description" in gaps

    def test_story_missing_unit_tests_has_gap(self):
        story = MagicMock(spec=Story)
        story.description = "Desc"
        story.acceptance_criteria = "AC"
        story.unit_test_cases = None
        story.ba_test_cases = ["scenario1"]

        is_complete, gaps = check_onboarding_completeness(story)
        assert is_complete is False
        assert "developer_unit_test_cases" in gaps

    def test_story_missing_ba_test_cases_has_gap(self):
        story = MagicMock(spec=Story)
        story.description = "Desc"
        story.acceptance_criteria = "AC"
        story.unit_test_cases = ["test1"]
        story.ba_test_cases = None

        is_complete, gaps = check_onboarding_completeness(story)
        assert is_complete is False
        assert "ba_tester_test_cases" in gaps

    def test_empty_test_cases_is_valid(self):
        """Empty lists (explicitly provided) should be valid — 'zero' is a state."""
        story = MagicMock(spec=Story)
        story.description = "Desc"
        story.acceptance_criteria = "AC"
        story.unit_test_cases = []
        story.ba_test_cases = []

        is_complete, gaps = check_onboarding_completeness(story)
        assert is_complete is True


class TestBugReasoningClassification:
    """Test bug-reasoning class suggestion (§7.4, FR-21)."""

    def test_keyword_suggests_silly_miss(self):
        bug = MagicMock(spec=Bug)
        bug.summary = "Typo in validation check, obvious oversight"
        bug.description = "Developer forgot to add null check"
        bug.severity = BugSeverity.MEDIUM

        result = _keyword_suggest_reasoning_class(bug)
        assert result["reasoning_class"] == BugReasoningClass.SILLY_MISS.value
        assert result["method"] == "keyword_rules"
        assert 0 < result["confidence"] <= 1.0

    def test_keyword_suggests_info_not_in_story(self):
        bug = MagicMock(spec=Bug)
        bug.summary = "Feature not specified in requirements"
        bug.description = "The story didn't contain needed information, unclear requirement"
        bug.severity = BugSeverity.HIGH

        result = _keyword_suggest_reasoning_class(bug)
        assert result["reasoning_class"] == BugReasoningClass.INFO_NOT_IN_STORY.value

    def test_keyword_suggests_missing_unit_test(self):
        bug = MagicMock(spec=Bug)
        bug.summary = "No unit test for this code path"
        bug.description = "Missing test coverage for validation"
        bug.severity = BugSeverity.MEDIUM

        result = _keyword_suggest_reasoning_class(bug)
        assert result["reasoning_class"] == BugReasoningClass.MISSING_UNIT_TEST.value

    def test_keyword_suggests_critical_miss(self):
        bug = MagicMock(spec=Bug)
        bug.summary = "Security vulnerability in authentication"
        bug.description = "Critical injection flaw in login"
        bug.severity = BugSeverity.CRITICAL

        result = _keyword_suggest_reasoning_class(bug)
        assert result["reasoning_class"] == BugReasoningClass.CRITICAL_MISS.value

    def test_keyword_suggests_wrong_test_cases(self):
        bug = MagicMock(spec=Bug)
        bug.summary = "Wrong test case for scenario"
        bug.description = "Incorrect test case missed the edge scenario"
        bug.severity = BugSeverity.MEDIUM

        result = _keyword_suggest_reasoning_class(bug)
        assert result["reasoning_class"] == BugReasoningClass.WRONG_TEST_CASES.value


class TestNormalizeRole:
    """Test role key normalization for ownership splits."""

    def test_normalize_ba(self):
        assert _normalize_role("ba") == "business_analyst"

    def test_normalize_dev(self):
        assert _normalize_role("dev") == "developer"

    def test_normalize_tester(self):
        assert _normalize_role("tester") == "tester"

    def test_normalize_automation(self):
        assert _normalize_role("automation") == "automation_engineer"

    def test_normalize_already_normalized(self):
        assert _normalize_role("developer") == "developer"


class TestDefaultDeductions:
    """Verify deduction table matches spec defaults."""

    def test_silly_miss_deduction(self):
        assert 0.5 <= DEFAULT_DEDUCTIONS[BugReasoningClass.SILLY_MISS.value] <= 1.0

    def test_critical_miss_deduction(self):
        assert 2.0 <= DEFAULT_DEDUCTIONS[BugReasoningClass.CRITICAL_MISS.value] <= 4.0

    def test_info_not_in_story_deduction(self):
        assert 1.5 <= DEFAULT_DEDUCTIONS[BugReasoningClass.INFO_NOT_IN_STORY.value] <= 3.0

    def test_missing_unit_test_deduction(self):
        assert 1.0 <= DEFAULT_DEDUCTIONS[BugReasoningClass.MISSING_UNIT_TEST.value] <= 2.0

    def test_wrong_test_cases_deduction(self):
        assert 1.0 <= DEFAULT_DEDUCTIONS[BugReasoningClass.WRONG_TEST_CASES.value] <= 2.0


class TestSeriousSeverities:
    """Verify serious severities match spec §5.5."""

    def test_critical_is_serious(self):
        assert BugSeverity.CRITICAL in SERIOUS_SEVERITIES

    def test_production_is_serious(self):
        assert BugSeverity.PRODUCTION in SERIOUS_SEVERITIES

    def test_security_is_serious(self):
        assert BugSeverity.SECURITY in SERIOUS_SEVERITIES

    def test_data_loss_is_serious(self):
        assert BugSeverity.DATA_LOSS in SERIOUS_SEVERITIES

    def test_medium_is_not_serious(self):
        assert BugSeverity.MEDIUM not in SERIOUS_SEVERITIES


class TestQualityClassEnum:
    """Test QualityClass enum values."""

    def test_high_value(self):
        assert QualityClass.HIGH.value == "high"

    def test_medium_value(self):
        assert QualityClass.MEDIUM.value == "medium"

    def test_low_value(self):
        assert QualityClass.LOW.value == "low"

    def test_insufficient_data_value(self):
        assert QualityClass.INSUFFICIENT_DATA.value == "insufficient_data"


class TestBugReasoningClassEnum:
    """Test BugReasoningClass enum values."""

    def test_all_classes_exist(self):
        expected = {"silly_miss", "critical_miss", "info_not_in_story", "missing_unit_test", "wrong_test_cases"}
        actual = {c.value for c in BugReasoningClass}
        assert actual == expected

    def test_five_classes(self):
        assert len(BugReasoningClass) == 5
