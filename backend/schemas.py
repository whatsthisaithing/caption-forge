"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


# ============================================================
# Folder Schemas
# ============================================================

class FolderCreate(BaseModel):
    """Request schema for creating a tracked folder."""
    path: str = Field(..., description="Absolute path to the folder")
    name: Optional[str] = Field(None, description="Display name (defaults to folder name)")
    recursive: bool = Field(True, description="Scan subfolders recursively")


class FolderUpdate(BaseModel):
    """Request schema for updating a tracked folder."""
    name: Optional[str] = None
    recursive: Optional[bool] = None
    enabled: Optional[bool] = None


class FolderResponse(BaseModel):
    """Response schema for a tracked folder."""
    id: str
    path: str
    name: str
    recursive: bool
    enabled: bool
    last_scan: Optional[datetime]
    file_count: int
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True


class FolderScanResult(BaseModel):
    """Response schema for folder scan operation."""
    folder_id: str
    files_found: int
    files_added: int
    files_updated: int
    files_removed: int
    thumbnails_generated: int
    captions_imported: int
    duration_seconds: float


# ============================================================
# File Schemas
# ============================================================

class FileResponse(BaseModel):
    """Response schema for a tracked file."""
    id: str
    folder_id: str
    filename: str
    relative_path: str
    absolute_path: str
    file_hash: Optional[str]
    width: Optional[int]
    height: Optional[int]
    file_size: Optional[int]
    format: Optional[str]
    exists: bool
    thumbnail_path: Optional[str]
    imported_caption: Optional[str]
    has_caption: bool = False  # Computed field indicating whether there's a caption
    file_modified: Optional[datetime]
    discovered_date: datetime
    
    class Config:
        from_attributes = True
    
    @model_validator(mode='after')
    def compute_has_caption(self):
        """Compute has_caption based on imported_caption."""
        if not self.has_caption and self.imported_caption:
            self.has_caption = True
        return self


class FileListResponse(BaseModel):
    """Response schema for paginated file list."""
    files: List[FileResponse]
    total: int
    page: int
    page_size: int


# ============================================================
# Dataset Schemas
# ============================================================

class DatasetCreate(BaseModel):
    """Request schema for creating a dataset."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class DatasetUpdate(BaseModel):
    """Request schema for updating a dataset."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    """Response schema for a dataset."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    file_count: int
    captioned_count: int
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True


class DatasetFilesAdd(BaseModel):
    """Request schema for adding files to a dataset."""
    file_ids: List[str] = Field(..., min_length=1)


class DatasetFilesRemove(BaseModel):
    """Request schema for removing files from a dataset."""
    file_ids: List[str] = Field(..., min_length=1)


class DatasetFileResponse(BaseModel):
    """Response schema for a file in a dataset context."""
    id: str
    dataset_id: str
    file_id: str
    order_index: int
    excluded: bool
    quality_score: Optional[float]
    quality_flags: Optional[str]
    added_date: datetime
    
    # Nested file info
    file: FileResponse
    
    class Config:
        from_attributes = True


class DatasetStatsResponse(BaseModel):
    """Response schema for dataset statistics."""
    dataset_id: str
    total_files: int
    excluded_files: int
    captioned_files: int
    uncaptioned_files: int
    avg_quality_score: Optional[float]
    total_size_bytes: int
    caption_sets: int


# ============================================================
# Caption Set Schemas
# ============================================================

class CaptionSetCreate(BaseModel):
    """Request schema for creating a caption set."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    style: str = Field("natural", pattern="^(natural|detailed|tags|custom)$")
    max_length: Optional[int] = Field(None, ge=10, le=10000)
    custom_prompt: Optional[str] = None
    trigger_phrase: Optional[str] = Field(None, max_length=500, description="Prefix for captions, e.g. 'Nova Chorus, a woman'")


class CaptionSetUpdate(BaseModel):
    """Request schema for updating a caption set."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    style: Optional[str] = Field(None, pattern="^(natural|detailed|tags|custom)$")
    max_length: Optional[int] = Field(None, ge=10, le=10000)
    custom_prompt: Optional[str] = None
    trigger_phrase: Optional[str] = Field(None, max_length=500)


class CaptionSetResponse(BaseModel):
    """Response schema for a caption set."""
    id: str
    dataset_id: str
    name: str
    description: Optional[str]
    style: str
    max_length: Optional[int]
    custom_prompt: Optional[str]
    trigger_phrase: Optional[str]
    caption_count: int
    created_date: datetime
    updated_date: datetime
    can_rollback_bulk_edit: Optional[bool] = False  # Will be populated by API
    
    class Config:
        from_attributes = True


# ============================================================
# Caption Schemas
# ============================================================

class CaptionCreate(BaseModel):
    """Request schema for creating/updating a caption."""
    file_id: str
    text: str = Field(..., min_length=1)
    source: str = Field("manual", pattern="^(manual|generated|imported)$")
    vision_model: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    quality_flags: Optional[List[str]] = None


class CaptionUpdate(BaseModel):
    """Request schema for updating a caption."""
    text: str = Field(..., min_length=1)


class CaptionResponse(BaseModel):
    """Response schema for a caption."""
    id: str
    caption_set_id: str
    file_id: str
    text: str
    source: str
    vision_model: Optional[str]
    quality_score: Optional[float]
    quality_flags: Optional[str]
    created_date: datetime
    updated_date: datetime
    
    class Config:
        from_attributes = True


class CaptionBatchUpdate(BaseModel):
    """Request schema for batch caption updates."""
    captions: List[CaptionCreate]


# ============================================================
# Bulk Edit Schemas
# ============================================================

class BulkEditOperation(BaseModel):
    """Configuration for a single bulk edit operation."""
    operation_type: str = Field(..., pattern="^(prepend|append|find_replace|trim|case_convert|remove_pattern)$")
    
    # For prepend/append
    text: Optional[str] = None
    
    # For find_replace
    find: Optional[str] = None
    replace: Optional[str] = None
    use_regex: bool = False
    case_sensitive: bool = True
    
    # For case_convert
    case_type: Optional[str] = Field(None, pattern="^(upper|lower|title|sentence)$")
    
    # For remove_pattern
    pattern: Optional[str] = None
    pattern_is_regex: bool = False


class BulkEditRequest(BaseModel):
    """Request schema for bulk caption editing."""
    operations: List[BulkEditOperation] = Field(..., min_length=1, description="List of operations to apply in order")
    
    @model_validator(mode='after')
    def validate_operations(self):
        """Validate that each operation has required fields."""
        for op in self.operations:
            if op.operation_type in ["prepend", "append"] and not op.text:
                raise ValueError(f"{op.operation_type} operation requires 'text' field")
            if op.operation_type == "find_replace" and (not op.find or op.replace is None):
                raise ValueError("find_replace operation requires 'find' and 'replace' fields")
            if op.operation_type == "case_convert" and not op.case_type:
                raise ValueError("case_convert operation requires 'case_type' field")
            if op.operation_type == "remove_pattern" and not op.pattern:
                raise ValueError("remove_pattern operation requires 'pattern' field")
        return self


class CaptionPreview(BaseModel):
    """Preview of a caption before and after bulk edit."""
    caption_id: str
    file_id: str
    before: str
    after: str


class BulkEditPreviewResponse(BaseModel):
    """Response schema for bulk edit preview."""
    total_captions: int
    affected_captions: int
    samples: List[CaptionPreview] = Field(..., description="Sample of affected captions (up to 5)")
    operation_summary: str = Field(..., description="Human-readable description of operations")


class BulkEditApplyResponse(BaseModel):
    """Response schema for applying bulk edits."""
    updated_count: int
    skipped_count: int
    error_count: int
    errors: List[Dict[str, str]] = Field(default_factory=list)


class BulkRollbackPreviewResponse(BaseModel):
    """Response schema for bulk rollback preview."""
    total_captions: int
    rollbackable_count: int
    skipped_count: int
    samples: List[Dict[str, Any]] = Field(default_factory=list, description="Sample of captions that will be rolled back")
    skipped_reasons: List[Dict[str, str]] = Field(default_factory=list, description="Reasons why some captions were skipped")


class BulkRollbackApplyResponse(BaseModel):
    """Response schema for applying bulk rollback."""
    rolled_back_count: int
    skipped_count: int
    error_count: int
    errors: List[Dict[str, str]] = Field(default_factory=list)


# ============================================================
# Caption Version History Schemas
# ============================================================

class CaptionVersionResponse(BaseModel):
    """Response schema for a caption version."""
    id: str
    caption_id: str
    version_number: int
    text: str
    operation: Optional[str]
    operation_description: Optional[str]
    source: Optional[str]
    vision_model: Optional[str]
    quality_score: Optional[float]
    quality_flags: Optional[str]
    created_date: datetime
    
    class Config:
        from_attributes = True


class CaptionWithHistoryResponse(BaseModel):
    """Response schema for a caption with its version history."""
    caption: CaptionResponse
    versions: List[CaptionVersionResponse]
    total_versions: int


# ============================================================
# Vision / Auto-Caption Schemas
# ============================================================

class VisionModelInfo(BaseModel):
    """Information about a vision model."""
    model_id: str
    name: str
    backend: str
    backend_model_name: str
    is_available: bool
    vram_gb: Optional[float] = None
    description: Optional[str] = None


class VisionGenerateRequest(BaseModel):
    """Request schema for single caption generation."""
    file_id: str
    style: str = Field("natural", pattern="^(natural|detailed|tags|custom)$")
    max_length: Optional[int] = Field(None, ge=10, le=10000)
    vision_model: Optional[str] = None
    vision_backend: Optional[str] = Field(None, pattern="^(ollama|lmstudio)$")
    custom_prompt: Optional[str] = None
    trigger_phrase: Optional[str] = Field(None, description="Caption must start with this phrase, e.g. 'Nova Chorus, a woman'")


class VisionGenerateResponse(BaseModel):
    """Response schema for caption generation."""
    caption: str
    quality_score: Optional[float]
    quality_flags: Optional[List[str]]
    processing_time_ms: int
    vision_model: str
    backend: str


class AutoCaptionJobCreate(BaseModel):
    """Request schema for starting auto-caption job."""
    vision_model: Optional[str] = None
    vision_backend: Optional[str] = Field(None, pattern="^(ollama|lmstudio)$")
    overwrite_existing: bool = False


class CaptionJobResponse(BaseModel):
    """Response schema for a caption job."""
    id: str
    caption_set_id: Optional[str]
    vision_model: str
    vision_backend: str
    status: str
    total_files: int
    completed_files: int
    failed_files: int
    current_file_id: Optional[str]
    last_error: Optional[str]
    created_date: datetime
    started_date: Optional[datetime]
    completed_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class CaptionJobProgress(BaseModel):
    """Progress update for caption generation job."""
    job_id: str
    status: str
    completed_files: int
    total_files: int
    failed_files: int
    percent_complete: float
    current_file: Optional[str]
    estimated_time_remaining_seconds: Optional[int]


# ============================================================
# Export Schemas
# ============================================================

class ExportRequest(BaseModel):
    """Request schema for dataset export."""
    caption_set_id: str
    export_type: str = Field("folder", pattern="^(folder|zip)$")
    export_path: Optional[str] = None  # Required for folder export
    
    # Filename options
    filename_prefix: Optional[str] = None  # Optional prefix for exported files (e.g., "Jeff" -> "Jeff-0001.jpg")
    numbering_start: int = Field(1, ge=0)
    numbering_padding: int = Field(6, ge=1, le=10)
    
    # Image processing
    image_format: Optional[str] = Field(None, pattern="^(jpeg|png|webp|original)$")
    target_resolution: Optional[int] = Field(None, ge=64, le=8192)
    max_resolution_longest_side: Optional[int] = Field(None, ge=64, le=16384, description="Optional max resolution for longest side - resizes images up or down")
    jpeg_quality: int = Field(95, ge=1, le=100)
    png_compression: int = Field(9, ge=0, le=9)
    strip_metadata: bool = True
    
    # Filtering
    min_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    exclude_flagged: Optional[List[str]] = None
    
    # Caption options
    caption_extension: str = Field("txt", pattern="^(txt|caption)$")
    include_manifest: bool = True


class ExportResponse(BaseModel):
    """Response schema for export operation."""
    export_id: str
    status: str
    export_path: Optional[str]
    estimated_files: int
    estimated_size_mb: Optional[float]


class ExportHistoryResponse(BaseModel):
    """Response schema for export history entry."""
    id: str
    dataset_id: Optional[str]
    caption_set_id: Optional[str]
    export_config: Optional[str]
    export_path: Optional[str]
    export_type: str
    file_count: int
    total_size_bytes: int
    status: str
    error_message: Optional[str]
    created_date: datetime
    completed_date: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================
# System Schemas
# ============================================================

class SystemStatsResponse(BaseModel):
    """Response schema for system statistics."""
    total_folders: int
    total_files: int
    total_datasets: int
    total_caption_sets: int
    total_captions: int
    database_size_bytes: int
    thumbnail_cache_size_bytes: int


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    version: str
    database_connected: bool
    ollama_available: bool
    lmstudio_available: bool
