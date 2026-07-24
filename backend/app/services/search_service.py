"""Search service - keyword and semantic search over stories, bugs, RCA (FR-10, Phase 2).

Implements hybrid search combining:
1. pgvector semantic similarity (when embeddings are available)
2. Keyword-based search with relevance scoring (always available)

Results are merged and ranked by a combined score.
"""

from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import Bug, Embedding, QualityEvent, Story
from app.schemas import SearchResult


def search_entities(
    db: Session, query: str, limit: int = 20, use_semantic: bool = True
) -> list[SearchResult]:
    """Hybrid search: combines semantic similarity with keyword matching.

    When embeddings are available and use_semantic=True, performs vector
    similarity search and merges with keyword results.
    Falls back to pure keyword search when embedding service is unavailable.
    """
    results = []

    # Always perform keyword search
    keyword_results = _keyword_search(db, query, limit)

    # Attempt semantic search if enabled
    semantic_results = []
    if use_semantic:
        semantic_results = _semantic_search(db, query, limit)

    # Merge results (semantic results get a boost)
    seen = set()
    merged = []

    # Add semantic results first (higher priority)
    for sr in semantic_results:
        key = (sr["entity_type"], sr["entity_id"])
        if key not in seen:
            seen.add(key)
            # Convert to SearchResult format
            merged.append(
                SearchResult(
                    entity_type=sr["entity_type"],
                    entity_id=sr["entity_id"],
                    title=sr.get("title", f"{sr['entity_type']}:{sr['entity_id']}"),
                    snippet=sr["chunk_text"][:200],
                    relevance_score=sr["similarity_score"],
                )
            )

    # Add keyword results that aren't already in semantic results
    for kr in keyword_results:
        key = (kr.entity_type, kr.entity_id)
        if key not in seen:
            seen.add(key)
            merged.append(kr)
        else:
            # Boost score for items found by both methods
            for m in merged:
                if m.entity_type == kr.entity_type and m.entity_id == kr.entity_id:
                    m.relevance_score = min(m.relevance_score * 1.2, 1.0)
                    break

    # Sort by relevance
    merged.sort(key=lambda r: r.relevance_score, reverse=True)
    return merged[:limit]


def _semantic_search(db: Session, query: str, limit: int) -> list[dict]:
    """Perform semantic search using embedding service."""
    try:
        from app.services.embedding_service import semantic_search as emb_search

        results = emb_search(db, query, limit=limit)

        # Enrich results with titles
        for result in results:
            result["title"] = _get_entity_title(db, result["entity_type"], result["entity_id"])

        return results
    except Exception:
        return []


def _get_entity_title(db: Session, entity_type: str, entity_id: int) -> str:
    """Get a human-readable title for an entity."""
    if entity_type == "story":
        story = db.query(Story).filter(Story.id == entity_id).first()
        if story:
            return f"[{story.story_id}] {story.title}"
    elif entity_type == "bug":
        bug = db.query(Bug).filter(Bug.id == entity_id).first()
        if bug:
            return f"[{bug.bug_id}] {bug.summary}"
    elif entity_type == "event":
        event = db.query(QualityEvent).filter(QualityEvent.id == entity_id).first()
        if event:
            return f"Quality Event: {event.event_type.value}"
    return f"{entity_type}:{entity_id}"


def _keyword_search(db: Session, query: str, limit: int) -> list[SearchResult]:
    """Keyword-based search with relevance scoring."""
    query_lower = query.lower()
    terms = query_lower.split()
    results = []

    # Search stories
    stories = (
        db.query(Story)
        .filter(
            or_(
                Story.title.ilike(f"%{query}%"),
                Story.acceptance_criteria.ilike(f"%{query}%"),
                Story.module.ilike(f"%{query}%"),
                Story.epic.ilike(f"%{query}%"),
            )
        )
        .limit(limit)
        .all()
    )

    for story in stories:
        score = _compute_relevance(
            terms,
            f"{story.title} {story.acceptance_criteria or ''} {story.module or ''}",
        )
        results.append(
            SearchResult(
                entity_type="story",
                entity_id=story.id,
                title=f"[{story.story_id}] {story.title}",
                snippet=_extract_snippet(
                    f"{story.acceptance_criteria or story.title}", query
                ),
                relevance_score=score,
            )
        )

    # Search bugs
    bugs = (
        db.query(Bug)
        .filter(
            or_(
                Bug.summary.ilike(f"%{query}%"),
                Bug.description.ilike(f"%{query}%"),
                Bug.root_cause.ilike(f"%{query}%"),
            )
        )
        .limit(limit)
        .all()
    )

    for bug in bugs:
        score = _compute_relevance(
            terms,
            f"{bug.summary} {bug.description or ''} {bug.root_cause or ''}",
        )
        results.append(
            SearchResult(
                entity_type="bug",
                entity_id=bug.id,
                title=f"[{bug.bug_id}] {bug.summary}",
                snippet=_extract_snippet(
                    f"{bug.description or bug.summary}", query
                ),
                relevance_score=score,
            )
        )

    # Search quality events
    events = (
        db.query(QualityEvent)
        .filter(QualityEvent.reason.ilike(f"%{query}%"))
        .limit(limit)
        .all()
    )

    for event in events:
        score = _compute_relevance(terms, event.reason)
        results.append(
            SearchResult(
                entity_type="event",
                entity_id=event.id,
                title=f"Quality Event: {event.event_type.value}",
                snippet=_extract_snippet(event.reason, query),
                relevance_score=score,
            )
        )

    # Sort by relevance
    results.sort(key=lambda r: r.relevance_score, reverse=True)
    return results[:limit]


def find_similar_bugs(db: Session, bug_id: int, limit: int = 10) -> list[SearchResult]:
    """Find bugs similar to the given bug using semantic similarity (FR-10).

    This implements the "find defects similar to BUG-1245" use case
    from Design Spec §7.3.
    """
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        return []

    # Use bug's text as the search query
    query_text = f"{bug.summary} {bug.description or ''}"

    # Try semantic search first
    try:
        from app.services.embedding_service import semantic_search as emb_search

        results = emb_search(db, query_text, entity_types=["bug"], limit=limit + 1)
        # Remove the source bug itself
        results = [r for r in results if not (r["entity_type"] == "bug" and r["entity_id"] == bug_id)]

        search_results = []
        for r in results[:limit]:
            similar_bug = db.query(Bug).filter(Bug.id == r["entity_id"]).first()
            if similar_bug:
                search_results.append(
                    SearchResult(
                        entity_type="bug",
                        entity_id=similar_bug.id,
                        title=f"[{similar_bug.bug_id}] {similar_bug.summary}",
                        snippet=r["chunk_text"][:200],
                        relevance_score=r["similarity_score"],
                    )
                )
        if search_results:
            return search_results
    except Exception:
        pass

    # Fall back to keyword search
    return _keyword_search(db, query_text, limit)


def _compute_relevance(terms: list[str], text: str) -> float:
    """Compute a simple relevance score based on term frequency."""
    if not text:
        return 0.0
    text_lower = text.lower()
    matches = sum(1 for term in terms if term in text_lower)
    return round(matches / max(len(terms), 1), 2)


def _extract_snippet(text: str, query: str, max_length: int = 200) -> str:
    """Extract a relevant snippet around the query match."""
    if not text:
        return ""
    query_lower = query.lower()
    text_lower = text.lower()
    idx = text_lower.find(query_lower)

    if idx == -1:
        return text[:max_length] + ("..." if len(text) > max_length else "")

    start = max(0, idx - 50)
    end = min(len(text), idx + len(query) + 150)
    snippet = text[start:end]

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet
