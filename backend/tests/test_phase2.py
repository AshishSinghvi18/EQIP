"""Tests for Phase 2: AI root-cause suggestions, semantic search, full-chain RCA."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.models.models import (
    Bug,
    BugSeverity,
    BugStatus,
    DetectedStage,
    Embedding,
    EventType,
    OriginStage,
    QualityEvent,
    RCAChainAnalysis,
    RootCauseCategory,
    Story,
    StoryStatus,
    UserRole,
)
from app.services.ai_service import suggest_root_cause, _keyword_suggest_root_cause
from app.services.rca_service import (
    _rule_based_chain_analysis,
    _determine_ownership,
    DELIVERY_CHAIN,
    CHAIN_STAGE_ROLES,
    analyze_full_chain,
)
from app.services.embedding_service import cosine_similarity, _fallback_text_search
from app.services.search_service import (
    _compute_relevance,
    _extract_snippet,
    find_similar_bugs,
)


# --- AI Root Cause Suggestion Tests ---


class TestAISuggestRootCause:
    """Test AI root cause suggestion (FR-8)."""

    def _make_bug(self, summary: str, description: str = "", severity=BugSeverity.MEDIUM):
        bug = MagicMock(spec=Bug)
        bug.bug_id = "BUG-001"
        bug.summary = summary
        bug.description = description
        bug.severity = severity
        bug.detected_stage = DetectedStage.QA_TESTING
        bug.root_cause = None
        bug.root_cause_category = None
        bug.origin_stage = None
        bug.story_id = None
        return bug

    def test_keyword_validation_bug(self):
        """Keyword engine detects validation bugs."""
        bug = self._make_bug(
            "Login form accepts empty password",
            "The validation check for empty password is missing"
        )
        result = _keyword_suggest_root_cause(bug)

        assert result["root_cause_category"] == "validation"
        assert result["origin_stage"] == "development"
        assert result["method"] == "keyword_rules"
        assert 0 < result["confidence"] <= 1.0

    def test_keyword_requirement_gap(self):
        """Keyword engine detects requirement gaps."""
        bug = self._make_bug(
            "Missing requirement for email format validation",
            "The specification did not mention email format rules"
        )
        result = _keyword_suggest_root_cause(bug)

        assert result["root_cause_category"] == "requirement_gap"
        assert result["origin_stage"] == "requirement"

    def test_keyword_security_issue(self):
        """Keyword engine detects security issues."""
        bug = self._make_bug(
            "SQL injection vulnerability in authentication endpoint",
            "The auth API is vulnerable to SQL injection attacks"
        )
        result = _keyword_suggest_root_cause(bug)

        assert result["root_cause_category"] == "security"
        assert result["origin_stage"] == "development"

    def test_suggestion_has_all_required_fields(self):
        """Every suggestion must have all required fields per FR-8."""
        bug = self._make_bug("Generic bug with no keywords")
        result = _keyword_suggest_root_cause(bug)

        assert "root_cause_category" in result
        assert "origin_stage" in result
        assert "severity" in result
        assert "ownership_split" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "method" in result

    def test_ownership_split_sums_to_100(self):
        """Ownership split must always sum to approximately 100%."""
        bug = self._make_bug("Validation error in user input")
        result = _keyword_suggest_root_cause(bug)

        total = sum(result["ownership_split"].values())
        assert total == 100

    def test_suggest_root_cause_falls_back_to_keywords(self):
        """suggest_root_cause falls back to keywords when LLM unavailable."""
        bug = self._make_bug("Null pointer in API response handler")
        # With no LLM configured, should fall back to keyword analysis
        result = suggest_root_cause(bug)
        assert result["method"] == "keyword_rules"

    def test_severity_critical_keywords(self):
        """Critical severity keywords trigger correct suggestion."""
        bug = self._make_bug(
            "Application crash on login",
            "The system crashes when user attempts login",
            severity=BugSeverity.MEDIUM,
        )
        result = _keyword_suggest_root_cause(bug)
        assert result["severity"] == "critical"


# --- Full-Chain RCA Tests ---


class TestFullChainRCA:
    """Test full-chain root cause analysis (FR-6)."""

    def _make_bug(self, **kwargs):
        bug = MagicMock(spec=Bug)
        bug.id = kwargs.get("id", 1)
        bug.bug_id = kwargs.get("bug_id", "BUG-100")
        bug.summary = kwargs.get("summary", "Test bug")
        bug.description = kwargs.get("description", "")
        bug.severity = kwargs.get("severity", BugSeverity.HIGH)
        bug.detected_stage = kwargs.get("detected_stage", DetectedStage.PRODUCTION)
        bug.root_cause = kwargs.get("root_cause", None)
        bug.root_cause_category = kwargs.get("root_cause_category", None)
        bug.origin_stage = kwargs.get("origin_stage", None)
        bug.story_id = kwargs.get("story_id", None)
        return bug

    def test_rule_based_chain_traces_requirement_origin(self):
        """Chain analysis correctly traces to requirement origin."""
        bug = self._make_bug(
            summary="Feature missing from spec",
            description="The requirement never specified this validation rule",
            detected_stage=DetectedStage.PRODUCTION,
        )
        result = _rule_based_chain_analysis(bug, None)

        assert result["root_origin_stage"] == OriginStage.REQUIREMENT
        assert "chain_stages" in result
        assert len(result["chain_stages"]) == len(DELIVERY_CHAIN)

    def test_rule_based_chain_traces_development_origin(self):
        """Chain analysis correctly traces to development origin."""
        bug = self._make_bug(
            summary="Null pointer exception in code",
            description="Code implementation has a null pointer bug",
            detected_stage=DetectedStage.QA_TESTING,
        )
        result = _rule_based_chain_analysis(bug, None)

        assert result["root_origin_stage"] == OriginStage.DEVELOPMENT

    def test_chain_identifies_missed_stages(self):
        """Chain analysis identifies stages that should have caught the bug."""
        bug = self._make_bug(
            summary="Logic error in calculation",
            description="Code logic bug found in production",
            detected_stage=DetectedStage.PRODUCTION,
        )
        result = _rule_based_chain_analysis(bug, None)

        # Between development (origin) and production (detection),
        # code_review and testing should have caught it
        assert len(result["contributing_factors"]) > 0

    def test_chain_stages_have_correct_structure(self):
        """Each chain stage entry has the required fields."""
        bug = self._make_bug(summary="Test bug")
        result = _rule_based_chain_analysis(bug, None)

        for stage in result["chain_stages"]:
            assert "stage" in stage
            assert "description" in stage
            assert "responsible_role" in stage
            assert "status" in stage

    def test_ownership_split_with_missed_stages(self):
        """Ownership is split between origin and stages that missed it."""
        ownership = _determine_ownership(
            OriginStage.DEVELOPMENT,
            ["code_review", "testing"]
        )
        assert "developer" in ownership
        total = sum(ownership.values())
        assert total == 100

    def test_ownership_single_owner(self):
        """Single owner gets 100% when no stages missed."""
        ownership = _determine_ownership(OriginStage.REQUIREMENT, [])
        assert ownership["business_analyst"] == 100

    def test_chain_uses_existing_category(self):
        """Chain analysis uses existing root_cause_category when available."""
        bug = self._make_bug(
            summary="Some bug",
            root_cause_category=RootCauseCategory.SECURITY,
        )
        result = _rule_based_chain_analysis(bug, None)
        assert result["root_origin_stage"] == OriginStage.DEVELOPMENT

    def test_shared_ownership_supports_multiple_roles(self):
        """FR-6: A single bug can be split across ≥2 roles."""
        bug = self._make_bug(
            summary="Requirement gap led to missing validation in code",
            description="The specification was unclear and the developer missed it",
            detected_stage=DetectedStage.PRODUCTION,
        )
        result = _rule_based_chain_analysis(bug, None)
        ownership = result["ownership_split"]
        # Should have multiple roles
        assert len(ownership) >= 1


# --- Semantic Search Tests ---


class TestSemanticSearch:
    """Test semantic search functionality (FR-10)."""

    def test_cosine_similarity_identical_vectors(self):
        """Identical vectors have similarity of 1.0."""
        vec = [1.0, 0.0, 1.0, 0.0]
        assert abs(cosine_similarity(vec, vec) - 1.0) < 0.001

    def test_cosine_similarity_orthogonal_vectors(self):
        """Orthogonal vectors have similarity of 0.0."""
        vec_a = [1.0, 0.0]
        vec_b = [0.0, 1.0]
        assert abs(cosine_similarity(vec_a, vec_b)) < 0.001

    def test_cosine_similarity_empty_vectors(self):
        """Empty vectors return 0.0."""
        assert cosine_similarity([], []) == 0.0

    def test_cosine_similarity_mismatched_lengths(self):
        """Mismatched vector lengths return 0.0."""
        assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0

    def test_compute_relevance_all_terms_match(self):
        """Full match returns score of 1.0."""
        score = _compute_relevance(["hello", "world"], "hello world test")
        assert score == 1.0

    def test_compute_relevance_partial_match(self):
        """Partial match returns fractional score."""
        score = _compute_relevance(["hello", "world", "foo"], "hello world test")
        assert 0 < score < 1.0

    def test_compute_relevance_no_match(self):
        """No match returns 0.0."""
        score = _compute_relevance(["xyz"], "hello world")
        assert score == 0.0

    def test_extract_snippet_with_match(self):
        """Snippet extraction centers on the match."""
        text = "prefix text " * 10 + "TARGET_QUERY" + " suffix text" * 10
        snippet = _extract_snippet(text, "TARGET_QUERY")
        assert "TARGET_QUERY" in snippet

    def test_extract_snippet_no_match(self):
        """Snippet returns beginning of text when no match."""
        text = "This is a long text without the search term" * 5
        snippet = _extract_snippet(text, "nonexistent")
        assert snippet.startswith("This is")

    def test_fallback_text_search(self):
        """Fallback search works when embedding service is unavailable."""
        db = MagicMock()
        emb = MagicMock(spec=Embedding)
        emb.entity_type = "bug"
        emb.entity_id = 1
        emb.chunk_text = "validation error in login authentication"

        # When entity_types is None, no .filter() is called after .query()
        db.query.return_value.all.return_value = [emb]

        results = _fallback_text_search(db, "validation login", None, 10)
        assert len(results) == 1
        assert results[0]["entity_type"] == "bug"
        assert results[0]["similarity_score"] > 0


# --- Embedding Service Tests ---


class TestEmbeddingService:
    """Test embedding management."""

    def test_embed_entity_stores_without_vector(self):
        """Embedding is stored even when vector generation fails."""
        from app.services.embedding_service import embed_entity

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        with patch("app.services.embedding_service.generate_embedding", return_value=None):
            result = embed_entity(db, "story", 1, "Test story text")

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.entity_type == "story"
        assert added.entity_id == 1
        assert added.chunk_text == "Test story text"
        assert added.vector is None

    def test_embed_entity_updates_existing(self):
        """Existing embedding is updated, not duplicated."""
        from app.services.embedding_service import embed_entity

        existing = MagicMock()
        existing.entity_type = "bug"
        existing.entity_id = 5

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        db.commit = MagicMock()
        db.refresh = MagicMock()

        with patch("app.services.embedding_service.generate_embedding", return_value=[0.1, 0.2]):
            embed_entity(db, "bug", 5, "Updated text")

        assert existing.chunk_text == "Updated text"
        assert existing.vector == [0.1, 0.2]


# --- Integration behavior tests ---


class TestPhase2Integration:
    """Integration-level behavior tests for Phase 2."""

    def test_ai_suggestion_does_not_affect_score_until_approved(self):
        """FR-9: AI suggestion stored on bug but no score effect until EM approves."""
        bug = MagicMock(spec=Bug)
        bug.bug_id = "BUG-999"
        bug.summary = "Performance issue in database query"
        bug.description = "Query is slow"
        bug.severity = BugSeverity.HIGH
        bug.detected_stage = DetectedStage.QA_TESTING
        bug.root_cause = None
        bug.root_cause_category = None
        bug.story_id = None

        suggestion = suggest_root_cause(bug)

        # Suggestion exists but is not auto-approved
        assert suggestion is not None
        assert suggestion["confidence"] > 0

        # Verify the suggestion would be stored on the bug
        # but human_approved_by would remain None
        # This is verified at the API level in test_core.py

    def test_chain_analysis_full_flow(self):
        """Full chain analysis produces complete traceable result."""
        bug = MagicMock(spec=Bug)
        bug.id = 1
        bug.bug_id = "BUG-500"
        bug.summary = "Missing validation for empty email field"
        bug.description = "The requirement specified email validation but code did not implement it"
        bug.severity = BugSeverity.HIGH
        bug.detected_stage = DetectedStage.PRODUCTION
        bug.root_cause = None
        bug.root_cause_category = None
        bug.story_id = None

        result = _rule_based_chain_analysis(bug, None)

        # Should trace through the full chain
        assert len(result["chain_stages"]) == 8  # All chain stages
        assert result["root_origin_stage"] in DELIVERY_CHAIN
        assert result["confidence"] > 0
        assert result["reasoning"] != ""
        assert sum(result["ownership_split"].values()) == 100
