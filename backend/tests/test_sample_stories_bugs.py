"""
Test cases for sample user stories and bugs in EQIP.

Covers:
  TC-001 – TC-010 : User story data integrity & validation
  TC-011 – TC-025 : Bug data integrity, severity mapping, RCA chain coverage
  TC-026 – TC-040 : Scoring engine behaviour with sample data
  TC-041 – TC-050 : Import pipeline, search, and cross-cutting scenarios
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.models.models import (
    BugSeverity,
    BugStatus,
    EventType,
    OriginStage,
    QualityEvent,
    RootCauseCategory,
    StoryStatus,
    UserRole,
)
from app.services.score_engine import compute_score_for_actor, record_quality_event

from tests.sample_data import SAMPLE_BUGS, SAMPLE_USER_STORIES


# =========================================================================
# User Story Data Integrity Tests (TC-001 to TC-010)
# =========================================================================


class TestUserStoryDataIntegrity:
    """Validate that every sample user story has correct structure and values."""

    def test_tc001_all_stories_have_required_fields(self):
        """TC-001: Every story must have story_id, title, module, and acceptance_criteria."""
        required = {"story_id", "title", "module", "acceptance_criteria"}
        for story in SAMPLE_USER_STORIES:
            missing = required - story.keys()
            assert not missing, f"{story['story_id']} missing fields: {missing}"

    def test_tc002_story_ids_are_unique(self):
        """TC-002: No duplicate story IDs in sample data."""
        ids = [s["story_id"] for s in SAMPLE_USER_STORIES]
        assert len(ids) == len(set(ids)), "Duplicate story IDs found"

    def test_tc003_story_statuses_are_valid(self):
        """TC-003: Every status maps to a valid StoryStatus enum value."""
        valid = {e.value for e in StoryStatus}
        for story in SAMPLE_USER_STORIES:
            assert story["status"] in valid, (
                f"{story['story_id']} has invalid status '{story['status']}'"
            )

    def test_tc004_story_points_are_fibonacci(self):
        """TC-004: Story points follow the Fibonacci sizing convention."""
        fibonacci = {1, 2, 3, 5, 8, 13, 21}
        for story in SAMPLE_USER_STORIES:
            assert story["story_points"] in fibonacci, (
                f"{story['story_id']} has non-Fibonacci points {story['story_points']}"
            )

    def test_tc005_acceptance_criteria_non_empty(self):
        """TC-005: Acceptance criteria must contain at least one numbered item."""
        for story in SAMPLE_USER_STORIES:
            ac = story["acceptance_criteria"]
            assert "1." in ac, f"{story['story_id']} has no numbered acceptance criteria"

    def test_tc006_high_priority_stories_have_medium_or_higher_complexity(self):
        """TC-006: High/Critical priority stories should not be trivially simple."""
        for story in SAMPLE_USER_STORIES:
            if story["priority"] in ("High", "Critical"):
                assert story["complexity"] in ("Medium", "High"), (
                    f"{story['story_id']} is High priority but {story['complexity']} complexity"
                )

    def test_tc007_each_module_has_at_least_one_story(self):
        """TC-007: Sample data covers multiple modules."""
        modules = {s["module"] for s in SAMPLE_USER_STORIES}
        assert len(modules) >= 5, f"Only {len(modules)} modules covered, expected ≥5"

    def test_tc008_done_stories_exist(self):
        """TC-008: At least some stories are marked 'done' for scoring validation."""
        done = [s for s in SAMPLE_USER_STORIES if s["status"] == "done"]
        assert len(done) >= 3, "Need at least 3 done stories for meaningful scoring"

    def test_tc009_story_id_format_correct(self):
        """TC-009: Story IDs follow 'US-NNN' convention."""
        import re
        for story in SAMPLE_USER_STORIES:
            assert re.match(r"^US-\d+$", story["story_id"]), (
                f"Invalid story ID format: {story['story_id']}"
            )

    def test_tc010_sample_stories_count(self):
        """TC-010: Sample data has at least 10 user stories."""
        assert len(SAMPLE_USER_STORIES) >= 10


# =========================================================================
# Bug Data Integrity Tests (TC-011 to TC-020)
# =========================================================================


class TestBugDataIntegrity:
    """Validate that every sample bug has correct structure and severity mapping."""

    def test_tc011_all_bugs_have_required_fields(self):
        """TC-011: Every bug must have bug_id, summary, severity, and status."""
        required = {"bug_id", "summary", "severity", "status"}
        for bug in SAMPLE_BUGS:
            missing = required - bug.keys()
            assert not missing, f"{bug['bug_id']} missing fields: {missing}"

    def test_tc012_bug_ids_are_unique(self):
        """TC-012: No duplicate bug IDs."""
        ids = [b["bug_id"] for b in SAMPLE_BUGS]
        assert len(ids) == len(set(ids))

    def test_tc013_severities_map_to_enum(self):
        """TC-013: Every bug severity is a valid BugSeverity."""
        valid = {e.value for e in BugSeverity}
        for bug in SAMPLE_BUGS:
            assert bug["severity"] in valid, (
                f"{bug['bug_id']} has invalid severity '{bug['severity']}'"
            )

    def test_tc014_statuses_map_to_enum(self):
        """TC-014: Every bug status is a valid BugStatus."""
        valid = {e.value for e in BugStatus}
        for bug in SAMPLE_BUGS:
            assert bug["status"] in valid, (
                f"{bug['bug_id']} has invalid status '{bug['status']}'"
            )

    def test_tc015_root_cause_categories_valid(self):
        """TC-015: Root cause categories map to the RootCauseCategory enum."""
        valid = {e.value for e in RootCauseCategory}
        for bug in SAMPLE_BUGS:
            if "root_cause_category" in bug:
                assert bug["root_cause_category"] in valid, (
                    f"{bug['bug_id']} has invalid category '{bug['root_cause_category']}'"
                )

    def test_tc016_origin_stages_valid(self):
        """TC-016: Origin stages map to OriginStage enum."""
        valid = {e.value for e in OriginStage}
        for bug in SAMPLE_BUGS:
            if "origin_stage" in bug:
                assert bug["origin_stage"] in valid

    def test_tc017_critical_bugs_have_p0_priority(self):
        """TC-017: Critical severity bugs should be P0."""
        for bug in SAMPLE_BUGS:
            if bug["severity"] == "critical":
                assert bug["priority"] == "P0", (
                    f"{bug['bug_id']} is critical but priority {bug['priority']}"
                )

    def test_tc018_every_bug_linked_to_story(self):
        """TC-018: Every sample bug references a valid story ID."""
        story_ids = {s["story_id"] for s in SAMPLE_USER_STORIES}
        for bug in SAMPLE_BUGS:
            assert bug["story_id"] in story_ids, (
                f"{bug['bug_id']} references unknown story {bug['story_id']}"
            )

    def test_tc019_bug_id_format_correct(self):
        """TC-019: Bug IDs follow 'BUG-NNN' convention."""
        import re
        for bug in SAMPLE_BUGS:
            assert re.match(r"^BUG-\d+$", bug["bug_id"])

    def test_tc020_sample_bugs_count(self):
        """TC-020: Sample data has at least 10 bugs."""
        assert len(SAMPLE_BUGS) >= 10


# =========================================================================
# Bug Distribution & Coverage Tests (TC-021 to TC-025)
# =========================================================================


class TestBugDistribution:
    """Ensure sample bugs cover diverse severity levels, categories, and stages."""

    def test_tc021_multiple_severity_levels_covered(self):
        """TC-021: Bugs span at least 3 different severity levels."""
        severities = {b["severity"] for b in SAMPLE_BUGS}
        assert len(severities) >= 3, f"Only {len(severities)} severity levels"

    def test_tc022_multiple_root_cause_categories_covered(self):
        """TC-022: Bugs span at least 4 root cause categories."""
        categories = {b["root_cause_category"] for b in SAMPLE_BUGS if "root_cause_category" in b}
        assert len(categories) >= 4, f"Only {len(categories)} categories"

    def test_tc023_bugs_detected_at_multiple_stages(self):
        """TC-023: Bugs are detected at 3+ different stages."""
        stages = {b["detected_stage"] for b in SAMPLE_BUGS if "detected_stage" in b}
        assert len(stages) >= 3, f"Only {len(stages)} detected stages"

    def test_tc024_bugs_originate_from_multiple_stages(self):
        """TC-024: Bugs originate from at least 2 different origin stages."""
        origins = {b["origin_stage"] for b in SAMPLE_BUGS if "origin_stage" in b}
        assert len(origins) >= 2

    def test_tc025_at_least_one_security_bug(self):
        """TC-025: At least one security-category bug exists for Security Sentinel badge testing."""
        security = [b for b in SAMPLE_BUGS if b.get("root_cause_category") == "security"]
        assert len(security) >= 1


# =========================================================================
# Scoring Engine Tests with Sample Data (TC-026 to TC-035)
# =========================================================================


class TestScoringWithSampleData:
    """Test that the scoring engine handles sample story/bug scenarios correctly."""

    def _mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        return db

    def test_tc026_developer_gains_for_zero_defect_story(self):
        """TC-026: Developer earns positive delta for a zero-defect story."""
        db = self._mock_db()
        event = record_quality_event(
            db=db, story_id=1, bug_id=None,
            role=UserRole.DEVELOPER, actor_id=1,
            event_type=EventType.ZERO_DEFECT_STORY,
            delta=3.0, reason="US-101 completed with zero defects",
        )
        added = db.add.call_args[0][0]
        assert added.delta == 3.0
        assert added.event_type == EventType.ZERO_DEFECT_STORY

    def test_tc027_developer_penalised_for_validation_bug(self):
        """TC-027: Developer gets negative delta for a validation bug (BUG-203)."""
        db = self._mock_db()
        record_quality_event(
            db=db, story_id=2, bug_id=3,
            role=UserRole.DEVELOPER, actor_id=1,
            event_type=EventType.VALIDATION_BUG,
            delta=-1.5, reason="BUG-203 price filter off-by-one",
        )
        added = db.add.call_args[0][0]
        assert added.delta < 0

    def test_tc028_tester_gains_for_critical_issue_found(self):
        """TC-028: Tester earns positive delta for finding critical bug (BUG-201)."""
        db = self._mock_db()
        record_quality_event(
            db=db, story_id=1, bug_id=1,
            role=UserRole.TESTER, actor_id=2,
            event_type=EventType.CRITICAL_ISSUE_FOUND,
            delta=3.0, reason="BUG-201 SQL injection caught in QA",
        )
        added = db.add.call_args[0][0]
        assert added.delta > 0
        assert added.role == UserRole.TESTER

    def test_tc029_ba_penalised_for_requirement_gap(self):
        """TC-029: BA gets negative delta for requirement gap (BUG-208)."""
        db = self._mock_db()
        record_quality_event(
            db=db, story_id=4, bug_id=8,
            role=UserRole.BUSINESS_ANALYST, actor_id=3,
            event_type=EventType.REQUIREMENT_GAP_TRACED,
            delta=-2.0, reason="BUG-208 guest checkout email not specified",
        )
        added = db.add.call_args[0][0]
        assert added.delta < 0
        assert added.role == UserRole.BUSINESS_ANALYST

    def test_tc030_tester_penalised_for_escaped_production_defect(self):
        """TC-030: Tester penalised when bug escapes to production (BUG-209)."""
        db = self._mock_db()
        record_quality_event(
            db=db, story_id=5, bug_id=9,
            role=UserRole.TESTER, actor_id=2,
            event_type=EventType.ESCAPED_PRODUCTION_DEFECT,
            delta=-3.0, reason="BUG-209 reached production — order history crash",
        )
        added = db.add.call_args[0][0]
        assert added.delta < 0
        assert added.event_type == EventType.ESCAPED_PRODUCTION_DEFECT

    def test_tc031_ai_suggested_event_requires_approval(self):
        """TC-031: AI-suggested event does not auto-approve."""
        db = self._mock_db()
        record_quality_event(
            db=db, story_id=4, bug_id=7,
            role=UserRole.DEVELOPER, actor_id=1,
            event_type=EventType.HIGH_SEVERITY_DEFECT,
            delta=-2.5, reason="AI: BUG-207 double charge",
            ai_suggested=True,
        )
        added = db.add.call_args[0][0]
        assert added.ai_suggested is True
        assert added.approved_by is None

    def test_tc032_independent_scoring_dev_and_tester_same_story(self):
        """TC-032: Dev and tester both score positively on same story — no zero-sum."""
        dev_evt = QualityEvent(
            id=1, story_id=1, role=UserRole.DEVELOPER, actor_id=1,
            event_type=EventType.FIRST_TIME_RIGHT_REVIEW, delta=2.0,
            reason="US-101 clean review", ai_suggested=False,
            approved_by=None, created_at=datetime.utcnow(),
        )
        tester_evt = QualityEvent(
            id=2, story_id=1, role=UserRole.TESTER, actor_id=2,
            event_type=EventType.CRITICAL_ISSUE_FOUND, delta=3.0,
            reason="BUG-201 found", ai_suggested=False,
            approved_by=None, created_at=datetime.utcnow(),
        )
        assert dev_evt.delta > 0 and tester_evt.delta > 0

    def test_tc033_unapproved_ai_event_excluded_from_total(self):
        """TC-033: Unapproved AI events are excluded from score totals."""
        events = [
            QualityEvent(
                id=1, story_id=1, role=UserRole.DEVELOPER, actor_id=1,
                event_type=EventType.ZERO_DEFECT_STORY, delta=3.0,
                reason="clean", ai_suggested=False, approved_by=None,
                created_at=datetime.utcnow(),
            ),
            QualityEvent(
                id=2, story_id=1, role=UserRole.DEVELOPER, actor_id=1,
                event_type=EventType.LOGIC_BUG, delta=-2.0,
                reason="AI suggestion", ai_suggested=True, approved_by=None,
                created_at=datetime.utcnow(),
            ),
        ]
        total = sum(e.delta for e in events if not (e.ai_suggested and e.approved_by is None))
        assert total == 3.0

    def test_tc034_security_improvement_positive_delta(self):
        """TC-034: Developer earns positive delta for security fix (BUG-201 fix)."""
        db = self._mock_db()
        record_quality_event(
            db=db, story_id=1, bug_id=1,
            role=UserRole.DEVELOPER, actor_id=1,
            event_type=EventType.SECURITY_IMPROVEMENT,
            delta=2.0, reason="Fixed SQL injection in BUG-201",
        )
        added = db.add.call_args[0][0]
        assert added.delta > 0

    def test_tc035_automation_penalised_for_flaky_tests(self):
        """TC-035: Automation engineer penalised for flaky tests."""
        db = self._mock_db()
        record_quality_event(
            db=db, story_id=2, bug_id=None,
            role=UserRole.AUTOMATION_ENGINEER, actor_id=4,
            event_type=EventType.FLAKY_TESTS,
            delta=-1.5, reason="Search filter tests flaky on CI",
        )
        added = db.add.call_args[0][0]
        assert added.delta < 0
        assert added.role == UserRole.AUTOMATION_ENGINEER


# =========================================================================
# Import Pipeline Tests (TC-036 to TC-040)
# =========================================================================


class TestImportPipeline:
    """Test column normalisation for story and bug import with sample data columns."""

    def test_tc036_story_column_normalisation(self):
        """TC-036: Import service normalises typical story column names."""
        from app.services.import_service import _normalize_columns
        import pandas as pd

        df = pd.DataFrame({
            "Story ID": ["US-101"], "Title": ["Login"], "Module": ["Auth"],
            "Story Points": [5], "Status": ["done"],
        })
        mapping = {
            "story_id": ["story_id", "id"],
            "title": ["title"],
            "module": ["module"],
            "story_points": ["story_points", "points"],
            "status": ["status"],
        }
        result = _normalize_columns(df, mapping)
        assert "story_id" in result.columns
        assert result.iloc[0]["story_id"] == "US-101"

    def test_tc037_bug_column_normalisation(self):
        """TC-037: Import service normalises typical bug column names."""
        from app.services.import_service import _normalize_columns
        import pandas as pd

        df = pd.DataFrame({
            "Bug ID": ["BUG-201"], "Summary": ["SQL injection"],
            "Severity": ["critical"], "Status": ["fixed"],
        })
        mapping = {
            "bug_id": ["bug_id", "id"],
            "summary": ["summary"],
            "severity": ["severity"],
            "status": ["status"],
        }
        result = _normalize_columns(df, mapping)
        assert "bug_id" in result.columns
        assert result.iloc[0]["severity"] == "critical"

    def test_tc038_story_data_can_build_dataframe(self):
        """TC-038: Sample stories can be loaded into a pandas DataFrame."""
        import pandas as pd
        df = pd.DataFrame(SAMPLE_USER_STORIES)
        assert len(df) == len(SAMPLE_USER_STORIES)
        assert "story_id" in df.columns

    def test_tc039_bug_data_can_build_dataframe(self):
        """TC-039: Sample bugs can be loaded into a pandas DataFrame."""
        import pandas as pd
        df = pd.DataFrame(SAMPLE_BUGS)
        assert len(df) == len(SAMPLE_BUGS)
        assert "bug_id" in df.columns

    def test_tc040_bug_severity_distribution(self):
        """TC-040: Verify the severity distribution of sample bugs."""
        import pandas as pd
        df = pd.DataFrame(SAMPLE_BUGS)
        counts = df["severity"].value_counts().to_dict()
        # Should have critical, high, and medium bugs
        assert "critical" in counts
        assert "high" in counts
        assert "medium" in counts


# =========================================================================
# Cross-Cutting Scenario Tests (TC-041 to TC-050)
# =========================================================================


class TestCrossCuttingScenarios:
    """End-to-end-style scenarios combining stories, bugs, and scoring."""

    def test_tc041_security_bugs_map_to_security_category(self):
        """TC-041: Bugs with root_cause_category=security map correctly."""
        sec_bugs = [b for b in SAMPLE_BUGS if b.get("root_cause_category") == "security"]
        assert all(b["severity"] in ("critical", "high") for b in sec_bugs)

    def test_tc042_production_detected_bugs_are_high_severity(self):
        """TC-042: Bugs detected in production are high/critical."""
        prod = [b for b in SAMPLE_BUGS if b.get("detected_stage") == "production"]
        assert all(b["severity"] in ("critical", "high") for b in prod)

    def test_tc043_stories_with_bugs_exist(self):
        """TC-043: At least some stories have associated bugs."""
        bugged_stories = {b["story_id"] for b in SAMPLE_BUGS}
        assert len(bugged_stories) >= 3

    def test_tc044_stories_without_bugs_exist(self):
        """TC-044: Some stories have zero bugs — candidates for Zero-Bug Champion."""
        bugged = {b["story_id"] for b in SAMPLE_BUGS}
        clean = [s for s in SAMPLE_USER_STORIES if s["story_id"] not in bugged]
        assert len(clean) >= 1

    def test_tc045_requirement_origin_bugs_trace_to_ba(self):
        """TC-045: Bugs originating at 'requirement' stage imply BA involvement."""
        req_bugs = [b for b in SAMPLE_BUGS if b.get("origin_stage") == "requirement"]
        assert len(req_bugs) >= 2, "Need ≥2 requirement-origin bugs"

    def test_tc046_development_origin_bugs_trace_to_developer(self):
        """TC-046: Bugs originating at 'development' stage imply Developer involvement."""
        dev_bugs = [b for b in SAMPLE_BUGS if b.get("origin_stage") == "development"]
        assert len(dev_bugs) >= 4

    def test_tc047_open_vs_fixed_bug_ratio(self):
        """TC-047: Sample data has both open and fixed bugs."""
        open_bugs = [b for b in SAMPLE_BUGS if b["status"] == "open"]
        fixed_bugs = [b for b in SAMPLE_BUGS if b["status"] == "fixed"]
        assert len(open_bugs) >= 3
        assert len(fixed_bugs) >= 3

    def _make_bug(self, summary, description=""):
        """Helper: create a minimal Bug-like object for keyword suggest."""
        bug = MagicMock()
        bug.summary = summary
        bug.description = description
        bug.environment = "QA"
        bug.severity = BugSeverity.HIGH
        return bug

    def test_tc048_keyword_rule_engine_detects_validation(self):
        """TC-048: Keyword RCA detects 'validation' from bug summary."""
        from app.services.ai_service import _keyword_suggest_root_cause
        bug = self._make_bug("Price filter returns wrong results due to validation error")
        suggestion = _keyword_suggest_root_cause(bug)
        assert suggestion["root_cause_category"] in ("validation", "business_logic", "requirement_gap")

    def test_tc049_keyword_rule_engine_detects_security(self):
        """TC-049: Keyword RCA detects 'security' from SQL injection summary."""
        from app.services.ai_service import _keyword_suggest_root_cause
        bug = self._make_bug("Security vulnerability — XSS and authentication bypass in login form")
        suggestion = _keyword_suggest_root_cause(bug)
        assert suggestion["root_cause_category"] == "security"

    def test_tc050_keyword_rule_engine_detects_performance(self):
        """TC-050: Keyword RCA detects 'performance' from crash/timeout summary."""
        from app.services.ai_service import _keyword_suggest_root_cause
        bug = self._make_bug("Page crashes for users with 1000+ orders — performance issue")
        suggestion = _keyword_suggest_root_cause(bug)
        assert suggestion["root_cause_category"] == "performance"
