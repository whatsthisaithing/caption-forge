"""Caption management service."""

import logging
import re
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from ..models import CaptionSet, Caption, CaptionVersion, TrackedFile
from ..schemas import CaptionSetUpdate, CaptionCreate, BulkEditRequest, BulkEditOperation

logger = logging.getLogger(__name__)


class CaptionService:
    """Service for managing captions and caption sets."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Caption Set methods
    def get_caption_set(self, caption_set_id: str) -> Optional[CaptionSet]:
        """Get a caption set by ID."""
        return self.db.query(CaptionSet).filter(CaptionSet.id == caption_set_id).first()
    
    def update_caption_set(self, caption_set_id: str, update: CaptionSetUpdate) -> Optional[CaptionSet]:
        """Update a caption set."""
        caption_set = self.get_caption_set(caption_set_id)
        if not caption_set:
            return None
        
        if update.name is not None:
            # Check for duplicate name in same dataset
            existing = self.db.query(CaptionSet).filter(
                CaptionSet.dataset_id == caption_set.dataset_id,
                CaptionSet.name == update.name,
                CaptionSet.id != caption_set_id
            ).first()
            if existing:
                raise ValueError(f"Caption set '{update.name}' already exists in this dataset")
            caption_set.name = update.name
        
        if update.description is not None:
            caption_set.description = update.description
        if update.style is not None:
            caption_set.style = update.style
        if update.max_length is not None:
            caption_set.max_length = update.max_length
        if update.custom_prompt is not None:
            caption_set.custom_prompt = update.custom_prompt
        if update.trigger_phrase is not None:
            caption_set.trigger_phrase = update.trigger_phrase
        
        self.db.commit()
        self.db.refresh(caption_set)
        return caption_set
    
    def delete_caption_set(self, caption_set_id: str) -> bool:
        """Delete a caption set and all its captions."""
        caption_set = self.get_caption_set(caption_set_id)
        if not caption_set:
            return False
        
        self.db.delete(caption_set)
        self.db.commit()
        logger.info(f"Deleted caption set: {caption_set.name}")
        return True
    
    # Caption methods
    def get_caption(self, caption_id: str) -> Optional[Caption]:
        """Get a caption by ID."""
        return self.db.query(Caption).filter(Caption.id == caption_id).first()
    
    def get_caption_for_file(self, caption_set_id: str, file_id: str) -> Optional[Caption]:
        """Get caption for a specific file in a caption set."""
        return self.db.query(Caption).filter(
            Caption.caption_set_id == caption_set_id,
            Caption.file_id == file_id
        ).first()
    
    def list_captions(
        self, 
        caption_set_id: str, 
        page: int = 1, 
        page_size: int = 50
    ) -> List[Caption]:
        """List captions in a caption set."""
        return self.db.query(Caption).filter(
            Caption.caption_set_id == caption_set_id
        ).order_by(Caption.created_date).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
    
    def create_or_update_caption(
        self, 
        caption_set_id: str, 
        data: CaptionCreate,
        create_version: bool = True
    ) -> Caption:
        """Create or update a caption for a file in a caption set."""
        import json
        
        # Verify file exists
        file = self.db.query(TrackedFile).filter(TrackedFile.id == data.file_id).first()
        if not file:
            raise ValueError(f"File not found: {data.file_id}")
        
        # Convert quality_flags list to JSON string if present
        quality_flags_json = None
        if data.quality_flags:
            quality_flags_json = json.dumps(data.quality_flags)
        
        # Check for existing caption
        caption = self.get_caption_for_file(caption_set_id, data.file_id)
        
        if caption:
            # Create version before updating (if requested)
            if create_version:
                self._create_version(
                    caption,
                    operation="manual_edit" if data.source == "manual" else f"auto_generate_{data.source}",
                    operation_description=f"Updated caption from {caption.source} to {data.source}"
                )
            
            # Update existing
            caption.text = data.text
            caption.source = data.source
            if data.vision_model is not None:
                caption.vision_model = data.vision_model
            if data.quality_score is not None:
                caption.quality_score = data.quality_score
            if quality_flags_json is not None:
                caption.quality_flags = quality_flags_json
        else:
            # Create new
            caption = Caption(
                caption_set_id=caption_set_id,
                file_id=data.file_id,
                text=data.text,
                source=data.source,
                vision_model=data.vision_model,
                quality_score=data.quality_score,
                quality_flags=quality_flags_json
            )
            self.db.add(caption)
            
            # Update caption set count
            caption_set = self.get_caption_set(caption_set_id)
            if caption_set:
                caption_set.caption_count = self.db.query(Caption).filter(
                    Caption.caption_set_id == caption_set_id
                ).count() + 1
        
        self.db.commit()
        self.db.refresh(caption)
        
        # Also update quality score on DatasetFile if quality data is provided
        if data.quality_score is not None:
            from ..models import DatasetFile, CaptionSet
            caption_set = self.get_caption_set(caption_set_id)
            if caption_set:
                dataset_file = self.db.query(DatasetFile).filter(
                    DatasetFile.file_id == data.file_id,
                    DatasetFile.dataset_id == caption_set.dataset_id
                ).first()
                if dataset_file:
                    dataset_file.quality_score = data.quality_score
                    if quality_flags_json is not None:
                        dataset_file.quality_flags = quality_flags_json
                    self.db.commit()
        
        return caption
    
    def update_caption(self, caption_id: str, text: str) -> Optional[Caption]:
        """Update a caption's text."""
        caption = self.get_caption(caption_id)
        if not caption:
            return None
        
        # Create version before update
        self._create_version(
            caption,
            operation="manual_edit",
            operation_description="Caption text updated"
        )
        
        caption.text = text
        caption.source = "manual"  # Mark as manually edited
        
        self.db.commit()
        self.db.refresh(caption)
        return caption
    
    def delete_caption(self, caption_id: str) -> bool:
        """Delete a caption."""
        caption = self.get_caption(caption_id)
        if not caption:
            return False
        
        caption_set_id = caption.caption_set_id
        self.db.delete(caption)
        
        # Update caption set count
        caption_set = self.get_caption_set(caption_set_id)
        if caption_set:
            caption_set.caption_count = self.db.query(Caption).filter(
                Caption.caption_set_id == caption_set_id
            ).count() - 1
        
        self.db.commit()
        return True
    
    def batch_update_captions(
        self, 
        caption_set_id: str, 
        captions: List[CaptionCreate]
    ) -> Dict[str, Any]:
        """Batch update multiple captions."""
        results = {
            "created": 0,
            "updated": 0,
            "errors": []
        }
        
        for caption_data in captions:
            try:
                existing = self.get_caption_for_file(caption_set_id, caption_data.file_id)
                self.create_or_update_caption(caption_set_id, caption_data)
                
                if existing:
                    results["updated"] += 1
                else:
                    results["created"] += 1
                    
            except Exception as e:
                results["errors"].append({
                    "file_id": caption_data.file_id,
                    "error": str(e)
                })
        
        return results
    
    def import_captions_from_files(self, caption_set_id: str, dataset_id: str) -> int:
        """Import captions from paired .txt files for all files in a dataset."""
        from ..models import DatasetFile
        
        imported = 0
        
        # Get all files in the dataset that have imported captions
        dataset_files = self.db.query(DatasetFile).join(
            TrackedFile, DatasetFile.file_id == TrackedFile.id
        ).filter(
            DatasetFile.dataset_id == dataset_id,
            TrackedFile.imported_caption.isnot(None)
        ).all()
        
        for df in dataset_files:
            file = df.file
            if not file.imported_caption:
                continue
            
            # Check if caption already exists
            existing = self.get_caption_for_file(caption_set_id, file.id)
            if existing:
                continue
            
            # Create caption from imported text
            caption = Caption(
                caption_set_id=caption_set_id,
                file_id=file.id,
                text=file.imported_caption,
                source="imported"
            )
            self.db.add(caption)
            imported += 1
        
        if imported > 0:
            # Update caption set count
            caption_set = self.get_caption_set(caption_set_id)
            if caption_set:
                caption_set.caption_count = self.db.query(Caption).filter(
                    Caption.caption_set_id == caption_set_id
                ).count()
            
            self.db.commit()
        
        logger.info(f"Imported {imported} captions from paired files")
        return imported
    
    # ============================================================
    # Version History Methods
    # ============================================================
    
    def _create_version(
        self, 
        caption: Caption, 
        operation: str = "manual_edit",
        operation_description: Optional[str] = None
    ) -> CaptionVersion:
        """Create a new version entry for a caption."""
        # Get the current max version number for this caption
        max_version = self.db.query(CaptionVersion).filter(
            CaptionVersion.caption_id == caption.id
        ).count()
        
        # Create new version
        version = CaptionVersion(
            caption_id=caption.id,
            version_number=max_version + 1,
            text=caption.text,
            operation=operation,
            operation_description=operation_description,
            source=caption.source,
            vision_model=caption.vision_model,
            quality_score=caption.quality_score,
            quality_flags=caption.quality_flags
        )
        self.db.add(version)
        self.db.flush()  # Don't commit yet, let caller decide
        
        return version
    
    def get_caption_history(self, caption_id: str) -> List[CaptionVersion]:
        """Get version history for a caption."""
        return self.db.query(CaptionVersion).filter(
            CaptionVersion.caption_id == caption_id
        ).order_by(CaptionVersion.version_number.desc()).all()
    
    def rollback_caption(self, caption_id: str, version_id: str) -> Optional[Caption]:
        """Rollback a caption to a specific version."""
        caption = self.get_caption(caption_id)
        if not caption:
            return None
        
        version = self.db.query(CaptionVersion).filter(
            CaptionVersion.id == version_id,
            CaptionVersion.caption_id == caption_id
        ).first()
        
        if not version:
            raise ValueError(f"Version not found: {version_id}")
        
        # Save current state as a new version before rollback
        self._create_version(
            caption, 
            operation="rollback", 
            operation_description=f"Rolled back to version {version.version_number}"
        )
        
        # Restore caption from version
        caption.text = version.text
        caption.source = version.source if version.source else caption.source
        caption.vision_model = version.vision_model
        caption.quality_score = version.quality_score
        caption.quality_flags = version.quality_flags
        
        self.db.commit()
        self.db.refresh(caption)
        
        logger.info(f"Rolled back caption {caption_id} to version {version.version_number}")
        return caption
    
    # ============================================================
    # Bulk Edit Methods
    # ============================================================
    
    def _apply_operation(self, text: str, operation: BulkEditOperation) -> str:
        """Apply a single bulk edit operation to text."""
        if operation.operation_type == "prepend":
            return operation.text + text
        
        elif operation.operation_type == "append":
            return text + operation.text
        
        elif operation.operation_type == "find_replace":
            if operation.use_regex:
                flags = 0 if operation.case_sensitive else re.IGNORECASE
                return re.sub(operation.find, operation.replace, text, flags=flags)
            else:
                if operation.case_sensitive:
                    return text.replace(operation.find, operation.replace)
                else:
                    # Case-insensitive replace
                    pattern = re.compile(re.escape(operation.find), re.IGNORECASE)
                    return pattern.sub(operation.replace, text)
        
        elif operation.operation_type == "trim":
            # Trim whitespace and normalize multiple spaces
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)
            return text
        
        elif operation.operation_type == "case_convert":
            if operation.case_type == "upper":
                return text.upper()
            elif operation.case_type == "lower":
                return text.lower()
            elif operation.case_type == "title":
                return text.title()
            elif operation.case_type == "sentence":
                # Capitalize first letter of each sentence
                return '. '.join(s.strip().capitalize() for s in text.split('.') if s.strip())
        
        elif operation.operation_type == "remove_pattern":
            if operation.pattern_is_regex:
                return re.sub(operation.pattern, '', text)
            else:
                return text.replace(operation.pattern, '')
        
        return text
    
    def _build_operation_summary(self, operations: List[BulkEditOperation]) -> str:
        """Build a human-readable summary of operations."""
        summaries = []
        for op in operations:
            if op.operation_type == "prepend":
                summaries.append(f"Prepend '{op.text[:20]}{'...' if len(op.text) > 20 else ''}'")
            elif op.operation_type == "append":
                summaries.append(f"Append '{op.text[:20]}{'...' if len(op.text) > 20 else ''}'")
            elif op.operation_type == "find_replace":
                regex_flag = " (regex)" if op.use_regex else ""
                summaries.append(f"Replace '{op.find}' with '{op.replace}'{regex_flag}")
            elif op.operation_type == "trim":
                summaries.append("Trim whitespace")
            elif op.operation_type == "case_convert":
                summaries.append(f"Convert to {op.case_type}case")
            elif op.operation_type == "remove_pattern":
                regex_flag = " (regex)" if op.pattern_is_regex else ""
                summaries.append(f"Remove pattern '{op.pattern}'{regex_flag}")
        
        return "; ".join(summaries)
    
    def preview_bulk_edit(
        self, 
        caption_set_id: str, 
        request: BulkEditRequest
    ) -> Dict[str, Any]:
        """Preview the effects of bulk edit operations without applying them."""
        captions = self.db.query(Caption).filter(
            Caption.caption_set_id == caption_set_id
        ).all()
        
        if not captions:
            return {
                "total_captions": 0,
                "affected_captions": 0,
                "samples": [],
                "operation_summary": self._build_operation_summary(request.operations)
            }
        
        # Apply operations to each caption and track changes
        affected = []
        samples = []
        
        for caption in captions:
            original_text = caption.text
            modified_text = original_text
            
            # Apply all operations in order
            for operation in request.operations:
                modified_text = self._apply_operation(modified_text, operation)
            
            # Track if changed
            if modified_text != original_text:
                affected.append({
                    "caption_id": caption.id,
                    "file_id": caption.file_id,
                    "before": original_text,
                    "after": modified_text
                })
        
        # Get up to 5 samples
        samples = affected[:5]
        
        return {
            "total_captions": len(captions),
            "affected_captions": len(affected),
            "samples": samples,
            "operation_summary": self._build_operation_summary(request.operations)
        }
    
    def apply_bulk_edit(
        self, 
        caption_set_id: str, 
        request: BulkEditRequest
    ) -> Dict[str, Any]:
        """Apply bulk edit operations to all captions in a caption set."""
        captions = self.db.query(Caption).filter(
            Caption.caption_set_id == caption_set_id
        ).all()
        
        updated_count = 0
        skipped_count = 0
        errors = []
        
        operation_summary = self._build_operation_summary(request.operations)
        
        for caption in captions:
            try:
                original_text = caption.text
                modified_text = original_text
                
                # Apply all operations in order
                for operation in request.operations:
                    modified_text = self._apply_operation(modified_text, operation)
                
                # Only update if changed
                if modified_text != original_text:
                    # Create version before update
                    self._create_version(
                        caption,
                        operation="bulk_edit",
                        operation_description=operation_summary
                    )
                    
                    # Update caption
                    caption.text = modified_text
                    caption.source = "manual"  # Mark as edited
                    updated_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"Error applying bulk edit to caption {caption.id}: {e}")
                errors.append({
                    "caption_id": caption.id,
                    "file_id": caption.file_id,
                    "error": str(e)
                })
        
        self.db.commit()
        
        logger.info(f"Bulk edit applied: {updated_count} updated, {skipped_count} skipped, {len(errors)} errors")
        
        return {
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "error_count": len(errors),
            "errors": errors
        }
    
    # ============================================================
    # Bulk Rollback Methods
    # ============================================================
    
    def can_rollback_last_bulk_edit(self, caption_set_id: str) -> bool:
        """Check if there are any captions with a recent bulk_edit that can be rolled back."""
        # Find captions where the most recent version is a bulk_edit
        # The version with operation="bulk_edit" contains the OLD text before the edit
        # So if this version exists, we CAN rollback to it (the version itself is the rollback target)
        captions = self.db.query(Caption).filter(
            Caption.caption_set_id == caption_set_id
        ).all()
        
        for caption in captions:
            # Get the most recent version
            latest_version = self.db.query(CaptionVersion).filter(
                CaptionVersion.caption_id == caption.id
            ).order_by(CaptionVersion.version_number.desc()).first()
            
            # If the latest version is a bulk_edit, we can rollback to it
            # (the version contains the pre-bulk-edit text)
            if latest_version and latest_version.operation == "bulk_edit":
                return True
        
        return False
    
    def preview_bulk_rollback(self, caption_set_id: str) -> Dict[str, Any]:
        """Preview what would happen if we rolled back the last bulk edit."""
        captions = self.db.query(Caption).filter(
            Caption.caption_set_id == caption_set_id
        ).all()
        
        rollbackable = []
        skipped = []
        
        for caption in captions:
            # Get the most recent version
            latest_version = self.db.query(CaptionVersion).filter(
                CaptionVersion.caption_id == caption.id
            ).order_by(CaptionVersion.version_number.desc()).first()
            
            if latest_version and latest_version.operation == "bulk_edit":
                # The bulk_edit version contains the pre-bulk-edit text (rollback target)
                rollbackable.append({
                    "caption_id": caption.id,
                    "file_id": caption.file_id,
                    "current_text": caption.text,
                    "rollback_to_text": latest_version.text,
                    "bulk_edit_description": latest_version.operation_description
                })
            else:
                # Not a bulk edit, skip
                if latest_version:
                    skipped.append({
                        "caption_id": caption.id,
                        "file_id": caption.file_id,
                        "reason": f"Last operation was '{latest_version.operation}', not 'bulk_edit'"
                    })
                else:
                    skipped.append({
                        "caption_id": caption.id,
                        "file_id": caption.file_id,
                        "reason": "No version history available"
                    })
        
        return {
            "total_captions": len(captions),
            "rollbackable_count": len(rollbackable),
            "skipped_count": len(skipped),
            "samples": rollbackable[:5],  # Show first 5 as preview
            "skipped_reasons": skipped[:5] if skipped else []
        }
    
    def apply_bulk_rollback(self, caption_set_id: str) -> Dict[str, Any]:
        """Rollback all captions where the last operation was a bulk_edit."""
        captions = self.db.query(Caption).filter(
            Caption.caption_set_id == caption_set_id
        ).all()
        
        rolled_back = 0
        skipped = 0
        errors = []
        
        for caption in captions:
            try:
                # Get the most recent version
                latest_version = self.db.query(CaptionVersion).filter(
                    CaptionVersion.caption_id == caption.id
                ).order_by(CaptionVersion.version_number.desc()).first()
                
                if not latest_version or latest_version.operation != "bulk_edit":
                    skipped += 1
                    continue
                
                # The bulk_edit version contains the pre-bulk-edit text
                # Save current state as a new version before rollback
                self._create_version(
                    caption,
                    operation="bulk_rollback",
                    operation_description=f"Rolled back bulk edit: {latest_version.operation_description}"
                )
                
                # Restore caption from the bulk_edit version (which has the old text)
                caption.text = latest_version.text
                caption.source = latest_version.source if latest_version.source else caption.source
                caption.vision_model = latest_version.vision_model
                caption.quality_score = latest_version.quality_score
                caption.quality_flags = latest_version.quality_flags
                
                rolled_back += 1
                
            except Exception as e:
                logger.error(f"Error rolling back caption {caption.id}: {e}")
                errors.append({
                    "caption_id": caption.id,
                    "file_id": caption.file_id,
                    "error": str(e)
                })
        
        self.db.commit()
        
        logger.info(f"Bulk rollback complete: {rolled_back} rolled back, {skipped} skipped, {len(errors)} errors")
        
        return {
            "rolled_back_count": rolled_back,
            "skipped_count": skipped,
            "error_count": len(errors),
            "errors": errors
        }

