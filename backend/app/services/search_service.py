"""Search service - keyword and semantic search over stories, bugs, RCA (FR-10, Phase 2).

In production, this would use pgvector embeddings. For now, implements
keyword-based search with relevance scoring.
"""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.models import Bug, QualityEvent, Story
from app.schemas import SearchResult


def search_entities(db: Session, query: str, limit: int = 20) -> list[SearchResult]:
    """Search stories, bugs, and quality events using keyword matching.

    In production with pgvector, this would compute embeddings and
    use cosine similarity. Currently uses keyword matching with ranking.
    """
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
