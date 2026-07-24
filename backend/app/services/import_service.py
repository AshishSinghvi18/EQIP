"""Import service for stories and bugs from Excel/CSV/JSON files (FR-2, FR-3)."""

import io
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import Bug, BugSeverity, BugStatus, Story, StoryStatus
from app.schemas import ImportResult


# Column mappings for flexible import
STORY_COLUMN_MAP = {
    "story_id": ["story_id", "id", "story id", "ticket_id", "ticket"],
    "title": ["title", "name", "summary", "story_title"],
    "epic": ["epic", "epic_name"],
    "module": ["module", "component", "area"],
    "priority": ["priority"],
    "complexity": ["complexity"],
    "story_points": ["story_points", "points", "sp"],
    "acceptance_criteria": ["acceptance_criteria", "ac", "criteria"],
    "status": ["status", "state"],
    "release": ["release", "version", "fix_version"],
    "environment": ["environment", "env"],
}

BUG_COLUMN_MAP = {
    "bug_id": ["bug_id", "id", "defect_id", "ticket_id"],
    "summary": ["summary", "title", "name"],
    "description": ["description", "details"],
    "severity": ["severity"],
    "priority": ["priority"],
    "environment": ["environment", "env"],
    "detected_stage": ["detected_stage", "found_in", "found_stage"],
    "root_cause": ["root_cause", "cause"],
    "root_cause_category": ["root_cause_category", "cause_category"],
    "origin_stage": ["origin_stage", "origin"],
    "bug_category": ["bug_category", "category", "type"],
    "status": ["status", "state"],
}


def _normalize_columns(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    """Map various column names to standardized names."""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    rename_map = {}
    for standard_name, alternatives in column_map.items():
        for alt in alternatives:
            if alt in df.columns and standard_name not in df.columns:
                rename_map[alt] = standard_name
                break
    return df.rename(columns=rename_map)


def _read_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """Read file content into a DataFrame based on file extension."""
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_content))
    elif filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_content))
    elif filename.endswith(".json"):
        return pd.read_json(io.BytesIO(file_content))
    else:
        raise ValueError(f"Unsupported file format: {filename}")


def import_stories(
    db: Session, file_content: bytes, filename: str, project_id: int
) -> ImportResult:
    """Import stories from Excel/CSV/JSON file."""
    df = _read_file(file_content, filename)
    df = _normalize_columns(df, STORY_COLUMN_MAP)

    imported = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            story_id = str(row.get("story_id", ""))
            title = str(row.get("title", ""))

            if not story_id or not title or story_id == "nan" or title == "nan":
                errors.append({"row": idx + 1, "error": "Missing story_id or title"})
                continue

            # Check for duplicate
            existing = db.query(Story).filter(Story.story_id == story_id).first()
            if existing:
                errors.append({"row": idx + 1, "error": f"Duplicate story_id: {story_id}"})
                continue

            story = Story(
                story_id=story_id,
                title=title,
                epic=_safe_str(row.get("epic")),
                project_id=project_id,
                module=_safe_str(row.get("module")),
                priority=_safe_str(row.get("priority")),
                complexity=_safe_str(row.get("complexity")),
                story_points=_safe_int(row.get("story_points")),
                acceptance_criteria=_safe_str(row.get("acceptance_criteria")),
                status=_parse_story_status(row.get("status")),
                release=_safe_str(row.get("release")),
                environment=_safe_str(row.get("environment")),
            )
            db.add(story)
            imported += 1
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)})

    db.commit()
    return ImportResult(total_rows=len(df), imported=imported, errors=errors)


def import_bugs(
    db: Session, file_content: bytes, filename: str
) -> ImportResult:
    """Import bugs from Excel/CSV/JSON file."""
    df = _read_file(file_content, filename)
    df = _normalize_columns(df, BUG_COLUMN_MAP)

    imported = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            bug_id = str(row.get("bug_id", ""))
            summary = str(row.get("summary", ""))

            if not bug_id or not summary or bug_id == "nan" or summary == "nan":
                errors.append({"row": idx + 1, "error": "Missing bug_id or summary"})
                continue

            existing = db.query(Bug).filter(Bug.bug_id == bug_id).first()
            if existing:
                errors.append({"row": idx + 1, "error": f"Duplicate bug_id: {bug_id}"})
                continue

            bug = Bug(
                bug_id=bug_id,
                summary=summary,
                description=_safe_str(row.get("description")),
                severity=_parse_severity(row.get("severity")),
                priority=_safe_str(row.get("priority")),
                environment=_safe_str(row.get("environment")),
                root_cause=_safe_str(row.get("root_cause")),
                bug_category=_safe_str(row.get("bug_category")),
                status=_parse_bug_status(row.get("status")),
            )
            db.add(bug)
            imported += 1
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e)})

    db.commit()
    return ImportResult(total_rows=len(df), imported=imported, errors=errors)


def _safe_str(val: Any) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val).strip() or None


def _safe_int(val: Any) -> int | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _parse_story_status(val: Any) -> StoryStatus:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return StoryStatus.BACKLOG
    val_str = str(val).strip().lower().replace(" ", "_")
    try:
        return StoryStatus(val_str)
    except ValueError:
        return StoryStatus.BACKLOG


def _parse_bug_status(val: Any) -> BugStatus:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return BugStatus.OPEN
    val_str = str(val).strip().lower().replace(" ", "_")
    try:
        return BugStatus(val_str)
    except ValueError:
        return BugStatus.OPEN


def _parse_severity(val: Any) -> BugSeverity:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return BugSeverity.GENERAL
    val_str = str(val).strip().lower().replace(" ", "_")
    try:
        return BugSeverity(val_str)
    except ValueError:
        return BugSeverity.GENERAL
