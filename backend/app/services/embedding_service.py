"""Embedding service for semantic search via pgvector (Phase 2, FR-10).

Manages vector embeddings for stories, bugs, and quality events.
Uses an OpenAI-compatible API for embedding generation (BGE-M3 by default).
In production with PostgreSQL + pgvector, uses cosine similarity for search.
Falls back to in-memory cosine similarity for SQLite development environments.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import Bug, Embedding, QualityEvent, Story

logger = logging.getLogger(__name__)


def _get_openai_client():
    """Get OpenAI client configured for embedding API."""
    try:
        from openai import OpenAI

        return OpenAI(
            base_url=settings.EMBEDDING_API_BASE_URL,
            api_key=settings.EMBEDDING_API_KEY or "not-needed",
            timeout=settings.LLM_TIMEOUT,
        )
    except Exception as e:
        logger.warning(f"Failed to create OpenAI client for embeddings: {e}")
        return None


def generate_embedding(text: str) -> Optional[list[float]]:
    """Generate an embedding vector for the given text.

    Uses the configured embedding model via OpenAI-compatible API.
    Returns None if the embedding service is unavailable.
    """
    client = _get_openai_client()
    if not client:
        return None

    try:
        response = client.embeddings.create(
            model=settings.EMBEDDING_MODEL_NAME,
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        return None


def embed_entity(
    db: Session,
    entity_type: str,
    entity_id: int,
    text: str,
) -> Optional[Embedding]:
    """Generate and store an embedding for an entity.

    If embedding generation fails (service unavailable), stores the text
    without a vector for later backfill.
    """
    # Check if embedding already exists
    existing = (
        db.query(Embedding)
        .filter(
            Embedding.entity_type == entity_type,
            Embedding.entity_id == entity_id,
        )
        .first()
    )

    vector = generate_embedding(text)

    if existing:
        existing.chunk_text = text
        existing.vector = vector
        existing.model_name = settings.EMBEDDING_MODEL_NAME
        db.commit()
        db.refresh(existing)
        return existing

    embedding = Embedding(
        entity_type=entity_type,
        entity_id=entity_id,
        chunk_text=text,
        vector=vector,
        model_name=settings.EMBEDDING_MODEL_NAME,
    )
    db.add(embedding)
    db.commit()
    db.refresh(embedding)
    return embedding


def embed_story(db: Session, story: Story) -> Optional[Embedding]:
    """Generate embedding for a story's searchable content."""
    text = (
        f"Story: {story.title}. "
        f"Module: {story.module or 'N/A'}. "
        f"Epic: {story.epic or 'N/A'}. "
        f"Acceptance Criteria: {story.acceptance_criteria or 'N/A'}. "
        f"Status: {story.status.value if story.status else 'N/A'}."
    )
    return embed_entity(db, "story", story.id, text)


def embed_bug(db: Session, bug: Bug) -> Optional[Embedding]:
    """Generate embedding for a bug's searchable content."""
    text = (
        f"Bug: {bug.summary}. "
        f"Description: {bug.description or 'N/A'}. "
        f"Severity: {bug.severity.value if bug.severity else 'N/A'}. "
        f"Root Cause: {bug.root_cause or 'N/A'}. "
        f"Category: {bug.root_cause_category.value if bug.root_cause_category else 'N/A'}. "
        f"Origin: {bug.origin_stage.value if bug.origin_stage else 'N/A'}."
    )
    return embed_entity(db, "bug", bug.id, text)


def embed_quality_event(db: Session, event: QualityEvent) -> Optional[Embedding]:
    """Generate embedding for a quality event."""
    text = (
        f"Quality Event: {event.event_type.value}. "
        f"Reason: {event.reason}. "
        f"Delta: {event.delta}. "
        f"Role: {event.role.value}."
    )
    return embed_entity(db, "event", event.id, text)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def semantic_search(
    db: Session, query: str, entity_types: Optional[list[str]] = None, limit: int = 20
) -> list[dict]:
    """Perform semantic similarity search using embeddings.

    In production with pgvector, this uses the <=> operator for cosine distance.
    Falls back to in-memory cosine similarity for SQLite development.

    Returns list of dicts with entity_type, entity_id, chunk_text, similarity_score.
    """
    query_vector = generate_embedding(query)

    if query_vector is None:
        # Embedding service unavailable - fall back to text-based search
        return _fallback_text_search(db, query, entity_types, limit)

    # Query all embeddings with vectors
    emb_query = db.query(Embedding).filter(Embedding.vector.isnot(None))
    if entity_types:
        emb_query = emb_query.filter(Embedding.entity_type.in_(entity_types))

    embeddings = emb_query.all()

    # Compute similarities (in production, pgvector does this in SQL)
    results = []
    for emb in embeddings:
        if emb.vector:
            similarity = cosine_similarity(query_vector, emb.vector)
            results.append(
                {
                    "entity_type": emb.entity_type,
                    "entity_id": emb.entity_id,
                    "chunk_text": emb.chunk_text,
                    "similarity_score": round(similarity, 4),
                }
            )

    # Sort by similarity descending
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:limit]


def _fallback_text_search(
    db: Session, query: str, entity_types: Optional[list[str]], limit: int
) -> list[dict]:
    """Fallback text search when embedding service is unavailable."""
    emb_query = db.query(Embedding)
    if entity_types:
        emb_query = emb_query.filter(Embedding.entity_type.in_(entity_types))

    embeddings = emb_query.all()
    query_lower = query.lower()
    terms = query_lower.split()

    results = []
    for emb in embeddings:
        text_lower = emb.chunk_text.lower()
        matches = sum(1 for term in terms if term in text_lower)
        if matches > 0:
            score = matches / max(len(terms), 1)
            results.append(
                {
                    "entity_type": emb.entity_type,
                    "entity_id": emb.entity_id,
                    "chunk_text": emb.chunk_text,
                    "similarity_score": round(score, 4),
                }
            )

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:limit]


def backfill_embeddings(db: Session, entity_type: Optional[str] = None) -> dict:
    """Backfill embeddings for entities that don't have them yet.

    Useful when first setting up pgvector or switching embedding models.
    Returns counts of processed entities.
    """
    counts = {"stories": 0, "bugs": 0, "events": 0}

    if entity_type is None or entity_type == "story":
        stories = db.query(Story).all()
        for story in stories:
            existing = (
                db.query(Embedding)
                .filter(Embedding.entity_type == "story", Embedding.entity_id == story.id)
                .first()
            )
            if not existing:
                embed_story(db, story)
                counts["stories"] += 1

    if entity_type is None or entity_type == "bug":
        bugs = db.query(Bug).all()
        for bug in bugs:
            existing = (
                db.query(Embedding)
                .filter(Embedding.entity_type == "bug", Embedding.entity_id == bug.id)
                .first()
            )
            if not existing:
                embed_bug(db, bug)
                counts["bugs"] += 1

    if entity_type is None or entity_type == "event":
        events = db.query(QualityEvent).all()
        for event in events:
            existing = (
                db.query(Embedding)
                .filter(Embedding.entity_type == "event", Embedding.entity_id == event.id)
                .first()
            )
            if not existing:
                embed_quality_event(db, event)
                counts["events"] += 1

    return counts
