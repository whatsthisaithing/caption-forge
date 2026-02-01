"""Caption management API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    CaptionSetUpdate, CaptionSetResponse,
    CaptionCreate, CaptionUpdate, CaptionResponse, CaptionBatchUpdate,
    BulkEditRequest, BulkEditPreviewResponse, BulkEditApplyResponse,
    BulkRollbackPreviewResponse, BulkRollbackApplyResponse,
    CaptionVersionResponse, CaptionWithHistoryResponse
)
from ..services.caption_service import CaptionService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["captions"])


# Caption Set endpoints (not nested under dataset)
@router.get("/caption-sets/{caption_set_id}", response_model=CaptionSetResponse)
def get_caption_set(caption_set_id: str, db: Session = Depends(get_db)):
    """Get a specific caption set by ID."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    # Check if bulk rollback is available
    result = caption_set.__dict__.copy()
    result['can_rollback_bulk_edit'] = service.can_rollback_last_bulk_edit(caption_set_id)
    return result


@router.put("/caption-sets/{caption_set_id}", response_model=CaptionSetResponse)
def update_caption_set(
    caption_set_id: str,
    update: CaptionSetUpdate,
    db: Session = Depends(get_db)
):
    """Update a caption set."""
    service = CaptionService(db)
    caption_set = service.update_caption_set(caption_set_id, update)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    return caption_set


@router.delete("/caption-sets/{caption_set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_caption_set(caption_set_id: str, db: Session = Depends(get_db)):
    """Delete a caption set."""
    service = CaptionService(db)
    if not service.delete_caption_set(caption_set_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")


# Caption endpoints
@router.get("/caption-sets/{caption_set_id}/captions", response_model=List[CaptionResponse])
def list_captions(
    caption_set_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """List all captions in a caption set."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    return service.list_captions(caption_set_id, page, page_size)


@router.post("/caption-sets/{caption_set_id}/captions", response_model=CaptionResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_caption(
    caption_set_id: str,
    caption: CaptionCreate,
    db: Session = Depends(get_db)
):
    """Create or update a caption for a file in a caption set."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    try:
        result = service.create_or_update_caption(caption_set_id, caption)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/caption-sets/{caption_set_id}/batch", status_code=status.HTTP_200_OK)
def batch_update_captions(
    caption_set_id: str,
    batch: CaptionBatchUpdate,
    db: Session = Depends(get_db)
):
    """Batch update multiple captions."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    results = service.batch_update_captions(caption_set_id, batch.captions)
    return {
        "updated": results["updated"],
        "created": results["created"],
        "errors": results["errors"]
    }


@router.get("/caption-sets/{caption_set_id}/files/{file_id}")
def get_caption_for_file(
    caption_set_id: str,
    file_id: str,
    db: Session = Depends(get_db)
):
    """Get caption for a specific file in a caption set. Returns the caption if exists, or file info with null caption."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    # Get the file details
    from ..models import TrackedFile
    file = db.query(TrackedFile).filter(TrackedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Get caption if it exists
    caption = service.get_caption_for_file(caption_set_id, file_id)
    
    # Parse quality flags from JSON if present
    quality_flags = None
    if caption and caption.quality_flags:
        import json
        try:
            quality_flags = json.loads(caption.quality_flags)
        except:
            quality_flags = None
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "imported_caption": file.imported_caption,
        "caption_set_id": caption_set_id,
        "caption_set_name": caption_set.name,
        "caption_set_max_length": caption_set.max_length,
        "caption": {
            "id": caption.id,
            "text": caption.text,
            "source": caption.source,
            "vision_model": caption.vision_model,
            "quality_score": caption.quality_score,
            "quality_flags": quality_flags,
            "created_date": caption.created_date.isoformat() if caption.created_date else None,
            "modified_date": caption.updated_date.isoformat() if caption.updated_date else None
        } if caption else None
    }


@router.get("/captions/{caption_id}", response_model=CaptionResponse)
def get_caption(caption_id: str, db: Session = Depends(get_db)):
    """Get a specific caption by ID."""
    service = CaptionService(db)
    caption = service.get_caption(caption_id)
    if not caption:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption not found")
    return caption


@router.put("/captions/{caption_id}", response_model=CaptionResponse)
def update_caption(
    caption_id: str,
    update: CaptionUpdate,
    db: Session = Depends(get_db)
):
    """Update a caption's text."""
    service = CaptionService(db)
    caption = service.update_caption(caption_id, update.text)
    if not caption:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption not found")
    return caption


@router.delete("/captions/{caption_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_caption(caption_id: str, db: Session = Depends(get_db)):
    """Delete a caption."""
    service = CaptionService(db)
    if not service.delete_caption(caption_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption not found")


# ============================================================
# Bulk Edit Endpoints
# ============================================================

@router.post("/caption-sets/{caption_set_id}/bulk-edit-preview", response_model=BulkEditPreviewResponse)
def preview_bulk_edit(
    caption_set_id: str,
    request: BulkEditRequest,
    db: Session = Depends(get_db)
):
    """Preview the effects of bulk edit operations on a caption set."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    try:
        result = service.preview_bulk_edit(caption_set_id, request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/caption-sets/{caption_set_id}/bulk-edit-apply", response_model=BulkEditApplyResponse)
def apply_bulk_edit(
    caption_set_id: str,
    request: BulkEditRequest,
    db: Session = Depends(get_db)
):
    """Apply bulk edit operations to all captions in a caption set."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    try:
        result = service.apply_bulk_edit(caption_set_id, request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================
# Bulk Rollback Endpoints
# ============================================================

@router.post("/caption-sets/{caption_set_id}/bulk-rollback-preview", response_model=BulkRollbackPreviewResponse)
def preview_bulk_rollback(
    caption_set_id: str,
    db: Session = Depends(get_db)
):
    """Preview what would happen if we rolled back the last bulk edit."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    result = service.preview_bulk_rollback(caption_set_id)
    return result


@router.post("/caption-sets/{caption_set_id}/bulk-rollback-apply", response_model=BulkRollbackApplyResponse)
def apply_bulk_rollback(
    caption_set_id: str,
    db: Session = Depends(get_db)
):
    """Rollback all captions where the last operation was a bulk_edit."""
    service = CaptionService(db)
    caption_set = service.get_caption_set(caption_set_id)
    if not caption_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption set not found")
    
    result = service.apply_bulk_rollback(caption_set_id)
    return result


# ============================================================
# Version History Endpoints
# ============================================================

@router.get("/captions/{caption_id}/history", response_model=CaptionWithHistoryResponse)
def get_caption_history(caption_id: str, db: Session = Depends(get_db)):
    """Get a caption with its full version history."""
    service = CaptionService(db)
    caption = service.get_caption(caption_id)
    if not caption:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption not found")
    
    versions = service.get_caption_history(caption_id)
    
    return {
        "caption": caption,
        "versions": versions,
        "total_versions": len(versions)
    }


@router.post("/captions/{caption_id}/rollback/{version_id}", response_model=CaptionResponse)
def rollback_caption(
    caption_id: str,
    version_id: str,
    db: Session = Depends(get_db)
):
    """Rollback a caption to a specific version."""
    service = CaptionService(db)
    
    try:
        caption = service.rollback_caption(caption_id, version_id)
        if not caption:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caption not found")
        return caption
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

