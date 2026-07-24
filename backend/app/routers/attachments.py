"""Attachment endpoints - Story reference documents (Word/PDF/Excel)."""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Attachment, Story
from app.schemas import AttachmentResponse

router = APIRouter(prefix="/attachments", tags=["attachments"])

# Storage directory for uploaded files
UPLOAD_DIR = Path(os.environ.get("EQIP_UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file types for reference documents
ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".doc": "doc",
    ".docx": "docx",
    ".xls": "xls",
    ".xlsx": "xlsx",
    ".csv": "csv",
    ".txt": "txt",
    ".md": "md",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/stories/{story_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(
    story_id: int,
    file: UploadFile = File(...),
    description: str | None = Query(None),
    uploaded_by: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Upload a reference document (Word/PDF/Excel) to a story.

    Supports: .pdf, .doc, .docx, .xls, .xlsx, .csv, .txt, .md
    Max file size: 50MB
    """
    # Validate story exists
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Validate file extension
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {list(ALLOWED_EXTENSIONS.keys())}",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB.")

    # Generate unique storage path
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    story_dir = UPLOAD_DIR / str(story_id)
    story_dir.mkdir(parents=True, exist_ok=True)
    file_path = story_dir / unique_name

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Create database record
    attachment = Attachment(
        story_id=story_id,
        filename=filename,
        file_type=ALLOWED_EXTENSIONS[ext],
        file_size=file_size,
        file_path=str(file_path),
        uploaded_by=uploaded_by,
        description=description,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/stories/{story_id}/attachments", response_model=list[AttachmentResponse])
def list_attachments(story_id: int, db: Session = Depends(get_db)):
    """List all reference documents attached to a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return db.query(Attachment).filter(Attachment.story_id == story_id).all()


@router.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int, db: Session = Depends(get_db)):
    """Download a reference document."""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.filename,
        media_type="application/octet-stream",
    )


@router.delete("/attachments/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: int, db: Session = Depends(get_db)):
    """Delete a reference document."""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Remove file from disk
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    db.delete(attachment)
    db.commit()
